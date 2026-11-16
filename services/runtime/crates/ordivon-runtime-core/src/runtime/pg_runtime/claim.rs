//! The Runtime PG database is the sole physical Workspace owner.
//! Harness may be in a different PostgreSQL database; a matching numeric
//! advisory lock in that database is NOT a Workspace close fence.
use super::*;
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};

fn schema_one() -> u32 {
    1
}

#[derive(Clone, Debug, Deserialize, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceClaimReserveRequest {
    #[serde(default = "schema_one")]
    pub schema_version: u32,
    pub workspace_id: String,
    pub client_request_id: String,
    pub run_ref: String,
    pub expected_source_state_digest: String,
}

#[derive(Clone, Debug, Deserialize, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceClaimKeyRequest {
    #[serde(default = "schema_one")]
    pub schema_version: u32,
    pub client_request_id: String,
}

#[derive(Clone, Debug, Deserialize, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceClaimProjection {
    pub schema_version: u32,
    pub claim_id: String,
    pub workspace_id: String,
    pub client_request_id: String,
    pub run_ref: String,
    /// Canonical native Runtime store carrier; bare workspaceId is not globally unique.
    pub store_root: String,
    pub source_repo: String,
    pub source_revision: String,
    pub source_state_digest_at_reserve: String,
    /// "held" is a physical pin, NOT proof the Harness Run is READY or
    /// permission to execute. The Harness/Gateway must validate their own
    /// semantic authorization before exposing a Tool grant.
    pub state: String,
    pub created_at_ms: i64,
    pub updated_at_ms: i64,
}

fn validate_key(schema: u32, principal: &str, client_request_id: &str) -> RuntimeResult<()> {
    if schema != 1 {
        return Err(RuntimeError::invalid(
            "schemaVersion must be 1",
            "schemaVersion",
        ));
    }
    crate::runtime::types::validate_logical_id(principal, "principal")?;
    crate::runtime::types::validate_client_request_id(client_request_id, "clientRequestId")?;
    Ok(())
}

fn query_claim<C: postgres::GenericClient>(
    client: &mut C,
    principal: &str,
    client_request_id: &str,
    lock: bool,
) -> RuntimeResult<Option<WorkspaceClaimProjection>> {
    let query = if lock {
        "SELECT claim_id, workspace_id, client_request_id, run_ref, store_root, source_repo,
                 source_revision, source_state_digest, state, created_at_ms, updated_at_ms
           FROM workspace_consumer_claims
          WHERE principal=$1 AND client_request_id=$2 FOR UPDATE"
    } else {
        "SELECT claim_id, workspace_id, client_request_id, run_ref, store_root, source_repo,
                 source_revision, source_state_digest, state, created_at_ms, updated_at_ms
           FROM workspace_consumer_claims
          WHERE principal=$1 AND client_request_id=$2"
    };
    client
        .query_opt(query, &[&principal, &client_request_id])
        .map_err(io)
        .map(|row| {
            row.map(|r| WorkspaceClaimProjection {
                schema_version: 1,
                claim_id: r.get(0),
                workspace_id: r.get(1),
                client_request_id: r.get(2),
                run_ref: r.get(3),
                store_root: r.get(4),
                source_repo: r.get(5),
                source_revision: r.get(6),
                source_state_digest_at_reserve: r.get(7),
                state: r.get(8),
                created_at_ms: r.get(9),
                updated_at_ms: r.get(10),
            })
        })
}

impl PgRuntime {
    /// A HELD claim is a durable physical pin. The Run remains semantic truth
    /// in Harness's independent DB: this method does not grant Tool execution.
    /// The same Runtime PG admission lock protects this insert AND NativeClose.
    pub fn reserve_workspace_claim(
        &self,
        principal: &str,
        request: &WorkspaceClaimReserveRequest,
    ) -> RuntimeResult<WorkspaceClaimProjection> {
        validate_key(
            request.schema_version,
            principal,
            &request.client_request_id,
        )?;
        crate::runtime::types::validate_logical_id(&request.run_ref, "runRef")?;
        universal::validate_id(&request.workspace_id, "workspaceId").map_err(io)?;
        if !request.expected_source_state_digest.starts_with("sha256:")
            || request.expected_source_state_digest.len() != 71
            || !request.expected_source_state_digest[7..]
                .bytes()
                .all(|x| x.is_ascii_hexdigit())
        {
            return Err(RuntimeError::invalid(
                "exact sha256 sourceStateDigest required",
                "expectedSourceStateDigest",
            ));
        }
        let store_root = self
            .config
            .executor
            .canonical_store_root()
            .map_err(io)?
            .to_string_lossy()
            .into_owned();
        let mut db = self.store()?;
        let mut tx = self.begin_workspace_effect_tx(&mut db)?;
        if let Some(existing) = query_claim(&mut tx, principal, &request.client_request_id, true)? {
            if existing.workspace_id != request.workspace_id
                || existing.store_root != store_root
                || existing.run_ref != request.run_ref
                || existing.source_state_digest_at_reserve != request.expected_source_state_digest
            {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::IdempotencyConflict,
                    "clientRequestId already binds a different physical Workspace/Run",
                    Some("clientRequestId"),
                    false,
                ));
            }
            tx.commit().map_err(io)?;
            return Ok(existing);
        }
        // This read MUST follow Runtime's own PG lock, NOT a cached Harness
        // preflight. A Closed/Opening record, missing Git directory, or stale
        // source identity must refuse claim creation, including after a crash
        // between Git removal and closed tombstone.
        let record = universal::load_workspace_record(&self.config.executor, &request.workspace_id)
            .map_err(super::super::error::map_universal_error)?;
        let physical_digest =
            universal::workspace_source_state_digest(&self.config.executor, &request.workspace_id)
                .map_err(io)?;
        if physical_digest != request.expected_source_state_digest {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RevisionMismatch,
                "Workspace source changed before Runtime-owned claim admission",
                Some("expectedSourceStateDigest"),
                false,
            ));
        }
        let id = format!("wclaim-{}", Uuid::now_v7());
        let time = now()?;
        tx.execute(
            "INSERT INTO workspace_consumer_claims
             (claim_id,principal,client_request_id,store_root,workspace_id,run_ref,source_repo,
              source_revision,source_state_digest,state,created_at_ms,updated_at_ms)
             VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,'held',$10,$10)",
            &[
                &id,
                &principal.to_owned(),
                &request.client_request_id,
                &store_root,
                &request.workspace_id,
                &request.run_ref,
                &record.source_repo,
                &record.source_revision,
                &physical_digest,
                &time,
            ],
        )
        .map_err(io)?;
        workspace_effect_commit(tx.commit(), "workspace.claim.reserve")?;
        Ok(WorkspaceClaimProjection {
            schema_version: 1,
            claim_id: id,
            workspace_id: request.workspace_id.clone(),
            client_request_id: request.client_request_id.clone(),
            run_ref: request.run_ref.clone(),
            store_root,
            source_repo: record.source_repo,
            source_revision: record.source_revision,
            source_state_digest_at_reserve: physical_digest,
            state: "held".to_string(),
            created_at_ms: time,
            updated_at_ms: time,
        })
    }

    /// Exact principal+request key is the recovery coordinate for lost
    /// COMMIT/MCP replies; never submit a different claim when result UNKNOWN.
    pub fn get_workspace_claim(
        &self,
        principal: &str,
        request: &WorkspaceClaimKeyRequest,
    ) -> RuntimeResult<WorkspaceClaimProjection> {
        validate_key(
            request.schema_version,
            principal,
            &request.client_request_id,
        )?;
        let store_root = self
            .config
            .executor
            .canonical_store_root()
            .map_err(io)?
            .to_string_lossy()
            .into_owned();
        let mut db = self.store()?;
        query_claim(&mut db.client, principal, &request.client_request_id, false)?
            .filter(|claim| claim.store_root == store_root)
            .ok_or_else(|| {
                RuntimeError::new(
                    RuntimeErrorCode::WorkspaceNotFound,
                    "no matching Runtime-owned Workspace Claim",
                    Some("clientRequestId"),
                    false,
                )
            })
    }

    /// This is a caller's consumer-release assertion, NOT an output finalizer.
    /// Source and ignored deliverables remain independent NativeClose gates.
    pub fn release_workspace_claim(
        &self,
        principal: &str,
        request: &WorkspaceClaimKeyRequest,
    ) -> RuntimeResult<WorkspaceClaimProjection> {
        validate_key(
            request.schema_version,
            principal,
            &request.client_request_id,
        )?;
        let store_root = self
            .config
            .executor
            .canonical_store_root()
            .map_err(io)?
            .to_string_lossy()
            .into_owned();
        let mut db = self.store()?;
        let mut tx = self.begin_workspace_effect_tx(&mut db)?;
        let mut existing = query_claim(&mut tx, principal, &request.client_request_id, true)?
            .filter(|claim| claim.store_root == store_root)
            .ok_or_else(|| {
                RuntimeError::new(
                    RuntimeErrorCode::WorkspaceNotFound,
                    "no matching Runtime-owned Workspace Claim to release",
                    Some("clientRequestId"),
                    false,
                )
            })?;
        if existing.state == "held" {
            let time = now()?;
            tx.execute(
                "UPDATE workspace_consumer_claims
                 SET state='released', updated_at_ms=$2
                 WHERE claim_id=$1 AND state='held'",
                &[&existing.claim_id, &time],
            )
            .map_err(io)?;
            existing.state = "released".to_string();
            existing.updated_at_ms = time;
        }
        workspace_effect_commit(tx.commit(), "workspace.claim.release")?;
        Ok(existing)
    }
}

#[cfg(test)]
mod claim_contract_tests {
    use super::*;
    #[test]
    fn invalid_identity_cannot_reach_pg_or_git() {
        assert!(validate_key(2, "principal", "request").is_err());
        assert!(validate_key(1, "", "request").is_err());
        assert!(validate_key(1, "principal", "bad\nrequest").is_err());
    }
}

#[cfg(test)]
mod claim_physical_pg_tests {
    use super::*;
    use std::{
        fs,
        path::Path,
        process::Command,
        sync::{Arc, Barrier},
        thread,
    };
    use tempfile::TempDir;

    struct DisposableSqlOwner {
        admin_dsn: String,
        schema: String,
        role: String,
    }
    impl Drop for DisposableSqlOwner {
        fn drop(&mut self) {
            if let Ok(mut pg) = postgres::Client::connect(&self.admin_dsn, postgres::NoTls) {
                let _ = pg.batch_execute(&format!(
                    "DROP SCHEMA IF EXISTS {} CASCADE; DROP ROLE IF EXISTS {}",
                    self.schema, self.role
                ));
            }
        }
    }

    fn git(repo: &Path, args: &[&str]) -> String {
        let mut command = Command::new("/usr/bin/git");
        command.arg("-C").arg(repo).args(args);
        for (key, _) in std::env::vars_os() {
            if key.to_string_lossy().starts_with("GIT_") {
                command.env_remove(key);
            }
        }
        command
            .env("GIT_AUTHOR_NAME", "Disposable Workspace Test")
            .env("GIT_AUTHOR_EMAIL", "test@localhost.invalid")
            .env("GIT_COMMITTER_NAME", "Disposable Workspace Test")
            .env("GIT_COMMITTER_EMAIL", "test@localhost.invalid");
        let out = command.output().expect("Git executable");
        assert!(
            out.status.success(),
            "git {:?} failed: {}",
            args,
            String::from_utf8_lossy(&out.stderr)
        );
        String::from_utf8(out.stdout).unwrap().trim().to_string()
    }

    /// Tests the Rust Runtime source path against physical Git+Postgres with
    /// the same independently qualified app-role restrictions as the server.
    /// Never connect this to production: requires a disposable PG18 database.
    #[test]
    #[ignore = "requires explicitly disposable ORDIVON_PG_TEST_DSN with CREATE ROLE/SCHEMA"]
    fn runtime_owned_pin_prevents_close_and_rejects_postclose_birth() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("test-only PostgreSQL DSN is explicitly required");
        let id = Uuid::now_v7().simple().to_string();
        let schema = format!("test_claim_{id}");
        let role = format!("test_claim_app_{id}");
        // A disposable Unix-only PostgreSQL test socket uses local trust;
        // the test must never invent or persist a reusable database password.
        let mut admin = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        let disposable_unix_only: bool = admin
            .query_one(
                "SELECT inet_server_addr() IS NULL AND current_setting('listen_addresses') = ''",
                &[],
            )
            .unwrap()
            .get(0);
        assert!(
            disposable_unix_only,
            "opt-in Claim test requires an isolated Unix-only PostgreSQL server"
        );
        admin
            .batch_execute(&format!(
                "CREATE ROLE {role} LOGIN;
             CREATE SCHEMA {schema};
             SET search_path TO {schema};"
            ))
            .unwrap();
        let _cleanup = DisposableSqlOwner {
            admin_dsn: dsn.clone(),
            schema: schema.clone(),
            role: role.clone(),
        };
        admin
            .batch_execute(include_str!("../../../sql/pg_fresh_epoch.sql"))
            .unwrap();
        // Native writer epoch has physical cluster and timeline identity.
        let epoch = admin
            .query_one(
                "SELECT (SELECT system_identifier::text FROM pg_control_system()),
                    (SELECT timeline_id FROM pg_control_checkpoint())",
                &[],
            )
            .unwrap();
        let source_sha = "a".repeat(64);
        let digest = crate::pg_admission::pg_writer_epoch_digest(
            &source_sha,
            &epoch.get::<_, String>(0),
            epoch.get::<_, i32>(1),
        );
        admin
            .execute(
                "INSERT INTO _stage_control(id,state,source_sha256,promotion_allowed)
             VALUES('source','QUALIFIED_WRITER',$1,true),
                   ('epoch','QUALIFIED_EPOCH',$2,true)",
                &[&source_sha, &digest],
            )
            .unwrap();
        admin
            .batch_execute(&format!(
                "GRANT USAGE ON SCHEMA {schema} TO {role};
             GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA {schema} TO {role};
             REVOKE ALL ON TABLE _stage_control FROM {role};
             GRANT SELECT,UPDATE(id) ON TABLE _stage_control TO {role};
             GRANT pg_monitor TO {role};"
            ))
            .unwrap();
        let app_dsn = format!("{dsn} user={role}");
        let root = TempDir::new().unwrap();
        let repo = root.path().join("source");
        fs::create_dir(&repo).unwrap();
        git(&repo, &["init", "-q"]);
        fs::write(repo.join("README.md"), "workspace pin physical fixture\n").unwrap();
        git(&repo, &["add", "README.md"]);
        git(&repo, &["commit", "-qm", "origin"]);
        let head = git(&repo, &["rev-parse", "HEAD"]);
        let config = UniversalExecutorConfig {
            store_root: root.path().join("runtime-store"),
            workspace_root: None,
            workspace_uid: None,
            workspace_gid: None,
            runner_path: Some("/usr/bin/true".into()),
            allowed_executable_roots: vec!["/usr/bin".into()],
            max_runtime_ms: 10000,
            max_output_bytes: 1024 * 1024,
        };
        let rt = PgRuntime::new(PgRuntimeConfig {
            dsn: app_dsn.clone(),
            schema: schema.clone(),
            source_sha256: source_sha.clone(),
            harness_issuer_schema: None,
            executor: config.clone(),
            workspace_headroom: vec![],
        })
        .expect("real qualified app role and Runtime PG epoch");
        let workspace_id = "ws-claim-real-git";
        rt.open_workspace(&GitWorkspaceCreateRequest {
            schema_version: 1,
            workspace_id: workspace_id.to_string(),
            source_repo: repo.to_string_lossy().into_owned(),
            source_revision: head,
        })
        .expect("native OPEN record with actual Git worktree");
        let exact = universal::workspace_source_state_digest(&config, workspace_id).unwrap();
        let req = WorkspaceClaimReserveRequest {
            schema_version: 1,
            workspace_id: workspace_id.into(),
            client_request_id: "caller-claim-1".into(),
            run_ref: "harness-run-A".into(),
            expected_source_state_digest: exact.clone(),
        };
        let claim = rt
            .reserve_workspace_claim("disposable-principal", &req)
            .unwrap();
        assert_eq!(claim.state, "held");
        let replay = rt
            .reserve_workspace_claim("disposable-principal", &req)
            .unwrap();
        assert_eq!(
            replay.claim_id, claim.claim_id,
            "exact request reuses durable claim"
        );
        let key = WorkspaceClaimKeyRequest {
            schema_version: 1,
            client_request_id: req.client_request_id.clone(),
        };
        assert_eq!(
            rt.get_workspace_claim("disposable-principal", &key)
                .unwrap()
                .claim_id,
            claim.claim_id,
            "response-loss readback uses same key"
        );
        let different = WorkspaceClaimReserveRequest {
            run_ref: "harness-run-B".into(),
            ..req.clone()
        };
        assert!(matches!(
            rt.reserve_workspace_claim("disposable-principal", &different),
            Err(RuntimeError {
                code: RuntimeErrorCode::IdempotencyConflict,
                ..
            })
        ));

        // A normal coding Run changes the Git source. A persistent Run claim
        // binds the original physical Workspace, NOT the mutable source hash.
        // The original source digest is only the admission-time CAS witness.
        let checkout = config.workspace_path(workspace_id);
        fs::write(
            checkout.join("README.md"),
            b"committed coding edit after HOLD\n",
        )
        .unwrap();
        git(&checkout, &["add", "README.md"]);
        git(
            &checkout,
            &["commit", "-qm", "coding result after held claim"],
        );
        let edited_digest = universal::workspace_source_state_digest(&config, workspace_id)
            .expect("current source after real native Git edit");
        assert_ne!(exact, edited_digest);
        let after_edit = rt
            .get_workspace_claim("disposable-principal", &key)
            .unwrap();
        assert_eq!(after_edit.claim_id, claim.claim_id);
        assert_eq!(after_edit.state, "held");
        assert_eq!(after_edit.source_state_digest_at_reserve, exact);
        assert!(
            matches!(
                rt.reserve_workspace_claim(
                    "disposable-principal",
                    &WorkspaceClaimReserveRequest {
                        expected_source_state_digest: edited_digest.clone(),
                        ..req.clone()
                    }
                ),
                Err(RuntimeError {
                    code: RuntimeErrorCode::IdempotencyConflict,
                    ..
                })
            ),
            "same Run must GET its original claim, never re-reserve with a moving Git digest"
        );

        // Two independent logical Runs share one physical Workspace. Releasing
        // Run A may not delete Run B's still-PAUSED physical substrate.
        let other_request = WorkspaceClaimReserveRequest {
            client_request_id: "caller-claim-B".into(),
            run_ref: "harness-run-B".into(),
            expected_source_state_digest: edited_digest.clone(),
            ..req.clone()
        };
        let other_claim = rt
            .reserve_workspace_claim("disposable-principal", &other_request)
            .unwrap();
        assert_eq!(other_claim.state, "held");
        let other_key = WorkspaceClaimKeyRequest {
            schema_version: 1,
            client_request_id: other_request.client_request_id.clone(),
        };
        let close = WorkspaceCloseRequest {
            schema_version: 1,
            workspace_id: workspace_id.into(),
            force: false,
            consumer_released: true,
            expected_source_state_digest: Some(edited_digest),
        };
        assert!(
            matches!(
                rt.close_workspace(&close),
                Err(RuntimeError {
                    code: RuntimeErrorCode::ConcurrencyLimit,
                    ..
                })
            ),
            "caller consumerReleased=true cannot override both held logical Runs"
        );
        assert_eq!(
            rt.release_workspace_claim("disposable-principal", &key)
                .unwrap()
                .state,
            "released"
        );
        assert_eq!(
            rt.release_workspace_claim("disposable-principal", &key)
                .unwrap()
                .state,
            "released",
            "release response-loss replay is idempotent"
        );
        assert!(
            matches!(
                rt.close_workspace(&close),
                Err(RuntimeError {
                    code: RuntimeErrorCode::ConcurrencyLimit,
                    ..
                })
            ),
            "Run B remains held even after Run A releases"
        );
        assert_eq!(
            rt.get_workspace_claim("disposable-principal", &other_key)
                .unwrap()
                .claim_id,
            other_claim.claim_id,
        );
        assert_eq!(
            rt.release_workspace_claim("disposable-principal", &other_key)
                .unwrap()
                .state,
            "released"
        );
        assert!(rt.close_workspace(&close).unwrap().removed);
        let after = WorkspaceClaimReserveRequest {
            client_request_id: "new-after-close".into(),
            run_ref: "new-harness-run".into(),
            ..req
        };
        assert!(
            rt.reserve_workspace_claim("disposable-principal", &after)
                .is_err(),
            "Native CLOSED tombstone must reject a born-after-close logical Run"
        );

        // Real interleaving: concurrent Reserve and NativeClose cannot BOTH
        // succeed because they share Runtime's own database advisory lock.
        let race_id = "ws-claim-race";
        rt.open_workspace(&GitWorkspaceCreateRequest {
            schema_version: 1,
            workspace_id: race_id.into(),
            source_repo: repo.to_string_lossy().into_owned(),
            source_revision: git(&repo, &["rev-parse", "HEAD"]),
        })
        .unwrap();
        let race_digest = universal::workspace_source_state_digest(&config, race_id).unwrap();
        let barrier = Arc::new(Barrier::new(3));
        let rt1 = rt.clone();
        let b1 = barrier.clone();
        let reserve = thread::spawn(move || {
            b1.wait();
            rt1.reserve_workspace_claim(
                "disposable-principal",
                &WorkspaceClaimReserveRequest {
                    schema_version: 1,
                    workspace_id: race_id.into(),
                    client_request_id: "race-reserve".into(),
                    run_ref: "race-run".into(),
                    expected_source_state_digest: race_digest,
                },
            )
            .is_ok()
        });
        let rt2 = rt.clone();
        let b2 = barrier.clone();
        let close_race = thread::spawn(move || {
            b2.wait();
            rt2.close_workspace(&WorkspaceCloseRequest {
                schema_version: 1,
                workspace_id: race_id.into(),
                force: false,
                consumer_released: true,
                expected_source_state_digest: None,
            })
            .is_ok()
        });
        barrier.wait();
        let reserved = reserve.join().unwrap();
        let closed = close_race.join().unwrap();
        assert_ne!(reserved, closed, "exactly one of conflicting effects wins");
        if reserved {
            rt.release_workspace_claim(
                "disposable-principal",
                &WorkspaceClaimKeyRequest {
                    schema_version: 1,
                    client_request_id: "race-reserve".into(),
                },
            )
            .unwrap();
            rt.close_workspace(&WorkspaceCloseRequest {
                schema_version: 1,
                workspace_id: race_id.into(),
                force: false,
                consumer_released: true,
                expected_source_state_digest: None,
            })
            .unwrap();
        }
        // Same Runtime PostgreSQL schema, DIFFERENT physical Store roots, and
        // exactly the same bare Workspace ID. A claim in Store B must not
        // globally block Store A, and a principal cannot get/release a B
        // claim through an A Runtime handle.
        let other = UniversalExecutorConfig {
            store_root: root.path().join("other-physical-runtime-store"),
            ..config.clone()
        };
        let second = PgRuntime::new(PgRuntimeConfig {
            dsn: app_dsn,
            schema: schema.clone(),
            source_sha256: source_sha,
            harness_issuer_schema: None,
            executor: other.clone(),
            workspace_headroom: vec![],
        })
        .unwrap();
        let shared_id = "ws-claim-scope-identical-id";
        let original = git(&repo, &["rev-parse", "HEAD"]);
        for runtime in [&rt, &second] {
            runtime
                .open_workspace(&GitWorkspaceCreateRequest {
                    schema_version: 1,
                    workspace_id: shared_id.to_string(),
                    source_repo: repo.to_string_lossy().into_owned(),
                    source_revision: original.clone(),
                })
                .unwrap();
        }
        let second_digest = universal::workspace_source_state_digest(&other, shared_id).unwrap();
        let scoped_request = WorkspaceClaimReserveRequest {
            schema_version: 1,
            workspace_id: shared_id.into(),
            client_request_id: "same-request-scope-test".into(),
            run_ref: "same-run-ref-test".into(),
            expected_source_state_digest: second_digest,
        };
        assert_eq!(
            second
                .reserve_workspace_claim("disposable-principal", &scoped_request)
                .unwrap()
                .state,
            "held"
        );
        let scoped_key = WorkspaceClaimKeyRequest {
            schema_version: 1,
            client_request_id: scoped_request.client_request_id.clone(),
        };
        assert!(
            rt.get_workspace_claim("disposable-principal", &scoped_key)
                .is_err(),
            "a foreign Store's claim must not be readable through the same PG role"
        );
        assert!(
            rt.release_workspace_claim("disposable-principal", &scoped_key)
                .is_err(),
            "a foreign Store's claim must not be released through the same PG role"
        );
        assert!(
            matches!(
                rt.reserve_workspace_claim("disposable-principal", &scoped_request),
                Err(RuntimeError {
                    code: RuntimeErrorCode::IdempotencyConflict,
                    ..
                })
            ),
            "same principal/request may not be replayed against a new store"
        );
        rt.close_workspace(&WorkspaceCloseRequest {
            schema_version: 1,
            workspace_id: shared_id.into(),
            force: false,
            consumer_released: true,
            expected_source_state_digest: None,
        })
        .unwrap();
        assert!(
            matches!(
                second.close_workspace(&WorkspaceCloseRequest {
                    schema_version: 1,
                    workspace_id: shared_id.into(),
                    force: false,
                    consumer_released: true,
                    expected_source_state_digest: None
                }),
                Err(RuntimeError {
                    code: RuntimeErrorCode::ConcurrencyLimit,
                    ..
                })
            ),
            "Store B native Workspace remains protected by its own held claim"
        );
        second
            .release_workspace_claim("disposable-principal", &scoped_key)
            .unwrap();
        second
            .close_workspace(&WorkspaceCloseRequest {
                schema_version: 1,
                workspace_id: shared_id.into(),
                force: false,
                consumer_released: true,
                expected_source_state_digest: None,
            })
            .unwrap();
        drop(second);
        drop(rt);
        drop(admin);
    }
}
