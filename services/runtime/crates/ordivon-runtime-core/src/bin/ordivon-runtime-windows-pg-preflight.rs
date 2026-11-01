//! Native Windows PostgreSQL cutover qualification. No service or Job is started.
//!
//! This is a physical, fail-closed probe, NOT a replacement for the Windows
//! Runtime. It deliberately has no SQL write or process dispatch capability.
#[cfg(windows)]
fn main() -> Result<(), Box<dyn std::error::Error>> {
    use ordivon_runtime_core::pg_admission::{PgAdmissionError, PgAdmissionStore};
    use serde_json::json;
    use sha2::Digest;
    use std::{env, fs::File, io::Read, path::Path};
    if std::env::args().skip(1).collect::<Vec<_>>() == ["--audit-admitted-job"] {
        let required = |key: &str| -> Result<String, Box<dyn std::error::Error>> {
            Ok(env::var(key).map_err(|_| format!("{key} missing"))?)
        };
        let output = ordivon_runtime_core::pg_windows_evidence::inspect_admitted_windows_pg_bundle(
            &required("ORDIVON_PG_DSN")?,
            &required("ORDIVON_PG_SCHEMA")?,
            &required("ORDIVON_PG_SOURCE_SHA256")?,
            &required("ORDIVON_PG_PRINCIPAL")?,
            &required("ORDIVON_PG_JOB_ID")?,
            Path::new(&required("ORDIVON_PG_STORE_ROOT")?),
        )?;
        let owner = ordivon_runtime_core::pg_windows_evidence::inspect_windows_pg_os_owner(&output);
        println!(
            "{}",
            json!({
                "kind":"ordivon.windows-pg-qualified-readback",
                "schemaVersion":1,
                "witness":output,
                "nativeOwnerState":owner,
                "executionReady":false,
                "postgresTerminalCommitted":false
            })
        );
        return Ok(());
    }
    if std::env::args().skip(1).collect::<Vec<_>>() == ["--self-test"] {
        println!(
            "{}",
            json!({
                "kind":"ordivon.windows-pg-preflight-self-test",
                "schemaVersion":1,
                "nativeWindows":cfg!(windows),
                "postgresConnected":false,
                "executionReady":false
            })
        );
        return Ok(());
    }
    let required = |key: &str| -> Result<String, Box<dyn std::error::Error>> {
        Ok(env::var(key).map_err(|_| format!("{key} missing"))?)
    };
    let dsn = required("ORDIVON_PG_DSN")?;
    let schema = required("ORDIVON_PG_SCHEMA")?;
    let source = required("ORDIVON_PG_SOURCE_SHA256")?;
    let launcher = required("ORDIVON_WINDOWS_LAUNCHER_PATH")?;
    if source.len() != 64 || !source.bytes().all(|c| c.is_ascii_hexdigit()) {
        return Err("source identity must be 64 hex characters".into());
    }
    let launcher_path = Path::new(&launcher);
    if !launcher_path.is_file() {
        return Err("Windows native launcher is missing".into());
    }
    // Existing PG contract includes schema-constraints and privilege checks.
    // Do not mistake a successful generic postgres connection for qualification.
    if let Err(err) = PgAdmissionStore::connect(&dsn, &schema) {
        let reason = match err {
            PgAdmissionError::InvalidInput => "invalid_schema",
            PgAdmissionError::Unqualified => "schema_unqualified",
            PgAdmissionError::Database(_) => "postgres_unavailable_or_unauthorized",
            _ => "postgres_contract_not_satisfied",
        };
        println!(
            "{}",
            json!({"kind":"ordivon.windows-pg-preflight",
            "schemaVersion":1,"pgSchemaQualified":false,
            "windowsNativeExecutablePresent":true,
            "executionReady":false,"reason":reason})
        );
        return Err("PostgreSQL physical qualification failed".into());
    }
    // Bound memory independently of launcher binary size.
    let mut file = File::open(launcher_path)?;
    let mut hash = sha2::Sha256::new();
    let mut chunk = [0_u8; 64 * 1024];
    loop {
        let count = file.read(&mut chunk)?;
        if count == 0 {
            break;
        }
        hash.update(&chunk[..count]);
    }
    let actual = hex::encode(hash.finalize());
    let digest = required("ORDIVON_WINDOWS_LAUNCHER_SHA256")?;
    if digest.to_ascii_lowercase() != actual {
        return Err("Windows native launcher digest does not match committed provider".into());
    }
    // Readiness is explicitly NOT proof of execution, recovery, or qualification
    // to promote the Windows service. Never advertise execution.windows here.
    println!(
        "{}",
        json!({"kind":"ordivon.windows-pg-preflight",
        "schemaVersion":1,"postgresSchemaReachable":true,
        "windowsLauncherDigestMatched":true,
        "sourceSha256":source,"executionReady":false,
        "reason":"windows_pg_execution_reconciliation_not_implemented"})
    );
    Ok(())
}
#[cfg(not(windows))]
fn main() {
    eprintln!("Windows PostgreSQL preflight is Windows-native only");
    std::process::exit(64);
}
