use ordivon_host_rust::{
    pg::{HostDbError, HostPg},
    work::{self, CommitSnapshot, CreateWork, WorkSnapshot, WorkState},
};
use serde_json::{json, Value};
use tokio_postgres::{types::Json, NoTls};
fn snapshot(frontier: &str, established: Vec<String>) -> WorkSnapshot {
    WorkSnapshot {
        objective: "synthetic".into(),
        frontier: frontier.into(),
        established,
        unresolved: vec![],
        rejected: vec![],
        constraints: vec![],
        next_actions: vec![],
        reference_refs: vec![],
    }
}
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let dsn = std::env::var("R23_PRIVATE_DSN")?;
    let args: Vec<String> = std::env::args().collect();
    let expected: i32 = args[1].parse()?;
    let pg = HostPg::try_new(dsn.clone())?;
    match pg.check_schema().await {
        Ok(v) if expected == 13 && v == 13 => println!("NATIVE_SCHEMA {expected} ACCEPTED"),
        Err(HostDbError::Schema(v)) if expected != 13 && v == expected => {
            println!("NATIVE_SCHEMA {expected} REJECTED")
        }
        other => panic!("unexpected schema gate {other:?}"),
    }
    if args.len() == 2 {
        return Ok(());
    }
    // Explicitly bypass only the staging service schema gate in a disposable test
    // by directly exercising public library functions. Not a deployment test.
    let expected: Value = serde_json::from_str(&std::fs::read_to_string(&args[2])?)?;
    let (mut client, connection) = tokio_postgres::connect(&dsn, NoTls).await?;
    tokio::spawn(async move { connection.await.expect("probe connection") });
    let create = |request: &str| CreateWork {
        work_ref: "work:r23-cross-language".into(),
        kind: "test".into(),
        actor_ref: "actor:agent:r23-cross-language".into(),
        initial_snapshot: snapshot("r1", vec!["repeat".into(), "repeat".into()]),
        client_request_id: request.into(),
    };
    let commit = CommitSnapshot {
        work_ref: "work:r23-cross-language".into(),
        expected_revision: 1,
        snapshot: snapshot("r2", vec!["a".into(), "a".into(), "b".into()]),
        actor_ref: "actor:agent:r23-cross-language".into(),
        state: WorkState::Open,
        client_request_id: "r23:compact".into(),
    };
    let legacy = work::create_work(&mut client, &create("r23:legacy")).await?;
    let compact = work::commit_snapshot(&mut client, &commit).await?;
    let later = work::create_work(&mut client, &create("r23:later")).await?;
    assert_eq!(legacy, expected["legacy"], "legacy replay must be equal");
    assert_eq!(compact, expected["compact"], "exact historical commit");
    assert_eq!(later, expected["later"], "exact historical later-create");
    if args.get(3).map(String::as_str) == Some("rollback") {
        println!("NATIVE_SCHEMA16_LEGACY_REPLAY 3/3");
        return Ok(());
    }
    let original: Value = client
        .query_one(
            "SELECT response FROM command_receipts WHERE client_request_id='r23:compact'",
            &[],
        )
        .await?
        .get::<_, Json<Value>>(0)
        .0;
    let mut damaged = original.clone();
    damaged["responseDigest"] = json!("sha256:bad");
    client
        .execute(
            "UPDATE command_receipts SET response=$1 WHERE client_request_id='r23:compact'",
            &[&Json(&damaged)],
        )
        .await?;
    assert!(matches!(
        work::commit_snapshot(&mut client, &commit).await,
        Err(work::WorkError::Integrity(_))
    ));
    client
        .execute(
            "UPDATE command_receipts SET response=$1 WHERE client_request_id='r23:compact'",
            &[&Json(&original)],
        )
        .await?;
    // An internally consistent tag pinned at the wrong historical revision
    // is still not evidence of the original commit request.
    let head = work::get_work(&mut client, "work:r23-cross-language", None).await?;
    let mut normalized = head.clone();
    normalized["admission"] = json!("existing");
    let mut wrong = original.clone();
    wrong["envelope"] = normalized.clone();
    wrong["envelope"]
        .as_object_mut()
        .unwrap()
        .remove("snapshot");
    wrong["responseDigest"] = json!(work::canonical_digest(&normalized)?);
    client.execute("UPDATE command_receipts SET response=$1,receipt_work_revision=3 WHERE client_request_id='r23:compact'", &[&Json(&wrong)]).await?;
    assert!(matches!(
        work::commit_snapshot(&mut client, &commit).await,
        Err(work::WorkError::Integrity(_))
    ));
    client.execute("UPDATE command_receipts SET response=$1,receipt_work_revision=2 WHERE client_request_id='r23:compact'", &[&Json(&original)]).await?;
    let payload:Value=client.query_one("SELECT payload FROM work_snapshots WHERE work_ref='work:r23-cross-language' AND revision=2",&[]).await?.get::<_,Json<Value>>(0).0;
    let mut corrupt = payload.clone();
    corrupt["frontier"] = json!("changed");
    client.execute("UPDATE work_snapshots SET payload=$1 WHERE work_ref='work:r23-cross-language' AND revision=2",&[&Json(&corrupt)]).await?;
    assert!(matches!(
        work::commit_snapshot(&mut client, &commit).await,
        Err(work::WorkError::Integrity(_))
    ));
    client.execute("UPDATE work_snapshots SET payload=$1 WHERE work_ref='work:r23-cross-language' AND revision=2",&[&Json(&payload)]).await?;
    assert_eq!(
        work::commit_snapshot(&mut client, &commit).await?,
        expected["compact"]
    );
    let mut changed = commit.clone();
    changed.snapshot.frontier = "changed".into();
    assert!(matches!(
        work::commit_snapshot(&mut client, &changed).await,
        Err(work::WorkError::Conflict(_))
    ));
    let new = work::create_work(&mut client, &create("r23:rust-legacy")).await?;
    assert_eq!(new["kind"], "ordivon.host-work");
    assert_eq!(new["revision"], 3);
    let mut reverse = new.clone();
    reverse["admission"] = json!("existing");
    std::fs::write(&args[3], serde_json::to_vec(&reverse)?)?;
    println!(
        "{}",
        json!({"legacyEqual":true,"compactEqual":true,"laterCreateEqual":true,"digestMutationRejected":true,"payloadMutationRejected":true,"wrongRootRejected":true,"rustLegacyWriter":true,"actualCompactKind":compact["kind"],"expectedCompactKind":expected["compact"]["kind"],"actualLaterKind":later["kind"],"expectedHistoricalRevision":expected["compact"]["revision"],"laterHistoricalRevision":expected["later"]["revision"],"requestCollisionRejected":true})
    );
    Ok(())
}
