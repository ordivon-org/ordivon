//! Offline initial import. No live writer cutover, authorization or retry.
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use tokio_postgres::{
    Client, Transaction,
    binary_copy::BinaryCopyInWriter,
    types::{ToSql, Type},
};

pub const OWNER_SCHEMA_V1: &str = include_str!("../schema/owner-v1.sql");

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "kind", content = "value", rename_all = "snake_case")]
pub enum Cell {
    Null,
    Text(Vec<u8>),
    Integer(i64),
    Blob(Vec<u8>),
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TableSnapshot {
    pub columns: Vec<String>,
    pub rows: Vec<Vec<Cell>>,
}
pub type Snapshot = BTreeMap<String, TableSnapshot>;

#[derive(Debug, thiserror::Error)]
pub enum ImportError {
    #[error("snapshot shape/type/representation mismatch: {0}")]
    Invalid(String),
    #[error("target does not match the exact source snapshot")]
    ReadbackMismatch,
    #[error("native import failed before commit: {0}")]
    Database(#[source] tokio_postgres::Error),
    #[error("rollback acknowledgement unavailable: {rollback}; initial failure: {cause}")]
    RollbackUnknown {
        cause: Box<ImportError>,
        rollback: tokio_postgres::Error,
    },
    #[error("import commit acknowledgement unavailable: {0}")]
    CommitUnknown(#[source] tokio_postgres::Error),
}

#[derive(Clone, Copy)]
enum Kind {
    Text,
    Integer,
    Blob,
}
#[derive(Clone, Copy)]
struct Column(&'static str, Kind, bool);
use Kind::{Blob as B, Integer as I, Text as T};
macro_rules! col {
    ($name:literal,$kind:ident) => {
        Column($name, $kind, false)
    };
    ($name:literal,$kind:ident,nullable) => {
        Column($name, $kind, true)
    };
}
struct Table(&'static str, &'static [Column]);
// FK-topological order, static identifiers only.
include!("migration_schema.rs");

fn validate(snapshot: &Snapshot) -> Result<(), ImportError> {
    if snapshot.len() != TABLES.len() {
        return Err(ImportError::Invalid("table inventory".into()));
    }
    for Table(name, columns) in TABLES {
        let table = snapshot
            .get(*name)
            .ok_or_else(|| ImportError::Invalid((*name).into()))?;
        if table
            .columns
            .iter()
            .map(String::as_str)
            .ne(columns.iter().map(|c| c.0))
        {
            return Err(ImportError::Invalid(format!("{name}: columns")));
        }
        let mut previous: Option<&[u8]> = None;
        for row in &table.rows {
            if row.len() != columns.len() {
                return Err(ImportError::Invalid(format!("{name}: row width")));
            }
            for (cell, Column(column, kind, nullable)) in row.iter().zip(*columns) {
                let valid = match (cell, kind) {
                    (Cell::Null, _) => *nullable,
                    (Cell::Text(v), Kind::Text) => {
                        !v.contains(&0) && std::str::from_utf8(v).is_ok()
                    }
                    (Cell::Integer(v), Kind::Integer) => {
                        (-9_007_199_254_740_991..=9_007_199_254_740_991).contains(v)
                    }
                    (Cell::Blob(_), Kind::Blob) => true,
                    _ => false,
                };
                if !valid {
                    return Err(ImportError::Invalid(format!("{name}.{column}")));
                }
            }
            let Cell::Text(key) = &row[0] else {
                return Err(ImportError::Invalid(format!("{name}: key")));
            };
            if previous.is_some_and(|p| p >= key.as_slice()) {
                return Err(ImportError::Invalid(format!(
                    "{name}: nonunique or unordered key"
                )));
            }
            previous = Some(key);
        }
    }
    Ok(())
}
fn param(cell: &Cell, kind: Kind) -> Box<dyn ToSql + Sync + Send> {
    match (cell, kind) {
        (Cell::Null, Kind::Text) => Box::new(None::<String>),
        (Cell::Null, Kind::Integer) => Box::new(None::<i64>),
        (Cell::Null, Kind::Blob) => Box::new(None::<Vec<u8>>),
        (Cell::Text(v), _) => Box::new(String::from_utf8(v.clone()).expect("validated UTF8")),
        (Cell::Integer(v), _) => Box::new(*v),
        (Cell::Blob(v), _) => Box::new(v.clone()),
    }
}
async fn install(
    tx: &Transaction<'_>,
    target_schema: &str,
    snapshot: &Snapshot,
) -> Result<(), ImportError> {
    let ready: bool = tx.query_one(
        "SELECT current_setting('server_encoding')='UTF8' AND current_schema()=$1 AND pg_my_temp_schema()=0 AND NOT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname=current_schema())",
        &[&target_schema],
    ).await.map_err(ImportError::Database)?.get(0);
    if !ready {
        return Err(ImportError::Invalid(
            "target schema must match explicit empty UTF8 destination and have no temporary namespace".into(),
        ));
    }
    // Bind unqualified fixed identifiers to the exact target, rather than
    // inheriting fallback schemas or a caller-created temporary table.
    tx.query_one(
        "SELECT set_config('search_path',quote_ident($1)||', pg_catalog, pg_temp',true)",
        &[&target_schema],
    )
    .await
    .map_err(ImportError::Database)?;
    // No IF NOT EXISTS or destructive cleanup. Existing tables fail closed.
    tx.batch_execute(OWNER_SCHEMA_V1)
        .await
        .map_err(ImportError::Database)?;
    for Table(name, cols) in TABLES {
        let names = cols.iter().map(|c| c.0).collect::<Vec<_>>().join(",");
        let types = cols
            .iter()
            .map(|c| match c.1 {
                Kind::Text => Type::TEXT,
                Kind::Integer => Type::INT8,
                Kind::Blob => Type::BYTEA,
            })
            .collect::<Vec<_>>();
        let sink = tx
            .copy_in(&format!("COPY {name} ({names}) FROM STDIN BINARY"))
            .await
            .map_err(ImportError::Database)?;
        let mut writer = std::pin::pin!(BinaryCopyInWriter::new(sink, &types));
        for row in &snapshot[*name].rows {
            let values = row
                .iter()
                .zip(*cols)
                .map(|(v, c)| param(v, c.1))
                .collect::<Vec<_>>();
            let args = values
                .iter()
                .map(|v| v.as_ref() as &(dyn ToSql + Sync))
                .collect::<Vec<_>>();
            writer
                .as_mut()
                .write(&args)
                .await
                .map_err(ImportError::Database)?;
        }
        let count = writer
            .as_mut()
            .finish()
            .await
            .map_err(ImportError::Database)?;
        if count != snapshot[*name].rows.len() as u64 {
            return Err(ImportError::ReadbackMismatch);
        }
    }
    tx.batch_execute("SET CONSTRAINTS ALL IMMEDIATE")
        .await
        .map_err(ImportError::Database)?;
    if read_snapshot(tx).await? != *snapshot {
        return Err(ImportError::ReadbackMismatch);
    }
    Ok(())
}
/// Read typed row facts from one caller-owned consistent snapshot.
pub async fn read_snapshot(tx: &Transaction<'_>) -> Result<Snapshot, ImportError> {
    let mut out = Snapshot::new();
    for Table(name, cols) in TABLES {
        let names = cols.iter().map(|c| c.0).collect::<Vec<_>>();
        let query = format!(
            "SELECT {} FROM {name} ORDER BY {} COLLATE \"C\"",
            names.join(","),
            names[0]
        );
        let mut rows = Vec::new();
        for row in tx.query(&query, &[]).await.map_err(ImportError::Database)? {
            let mut result = Vec::new();
            for (j, Column(_, kind, _)) in cols.iter().enumerate() {
                let cell = match kind {
                    Kind::Text => row
                        .try_get::<_, Option<String>>(j)
                        .map(|v| v.map(|x| Cell::Text(x.into_bytes())).unwrap_or(Cell::Null)),
                    Kind::Integer => row
                        .try_get::<_, Option<i64>>(j)
                        .map(|v| v.map(Cell::Integer).unwrap_or(Cell::Null)),
                    Kind::Blob => row
                        .try_get::<_, Option<Vec<u8>>>(j)
                        .map(|v| v.map(Cell::Blob).unwrap_or(Cell::Null)),
                }
                .map_err(ImportError::Database)?;
                result.push(cell);
            }
            rows.push(result);
        }
        out.insert(
            (*name).into(),
            TableSnapshot {
                columns: names.into_iter().map(str::to_owned).collect(),
                rows,
            },
        );
    }
    Ok(out)
}
/// Installs an exact initial snapshot using caller-owned isolated destination.
/// Source quiescence, destination exclusivity and connection disposal after
/// UNKNOWN are caller obligations. No streaming or live migration claim.
pub async fn import_initial(
    client: &mut Client,
    target_schema: &str,
    snapshot: &Snapshot,
) -> Result<(), ImportError> {
    if target_schema.is_empty() || target_schema.contains('\0') {
        return Err(ImportError::Invalid("target schema identity".into()));
    }
    validate(snapshot)?;
    let tx = client.transaction().await.map_err(ImportError::Database)?;
    if let Err(cause) = install(&tx, target_schema, snapshot).await {
        return match tx.rollback().await {
            Ok(()) => Err(cause),
            Err(rollback) => Err(ImportError::RollbackUnknown {
                cause: Box::new(cause),
                rollback,
            }),
        };
    }
    tx.commit().await.map_err(ImportError::CommitUnknown)
}

/// Additive V2 login eligibility/completion state. Apply under exclusive owner migration.
pub const LOGIN_COMPLETION_SCHEMA_V2: &str = include_str!("../schema/owner-v2-login.sql");
