use ordivon_runtime_core::{
    inspect_job, inspect_registry, inspect_registry_activity, inspect_registry_archive,
    inspect_registry_markers, inspect_registry_status, inspect_registry_workspace_activity,
    inspect_workspace, summarize_experience, RuntimeInspectionConfig,
    RuntimeWorkspaceInspectionConfig, DEFAULT_INSPECTION_EVENT_LIMIT,
    DEFAULT_WORKSPACE_INSPECTION_JOB_LIMIT, MAX_ARCHIVE_SAMPLE_LIMIT, MAX_INSPECTION_EVENT_LIMIT,
    MAX_WORKSPACE_INSPECTION_JOB_LIMIT,
};
use std::env;
use std::path::PathBuf;

fn main() {
    if let Err(message) = run() {
        eprintln!("{message}");
        std::process::exit(1);
    }
}

fn run() -> Result<(), String> {
    let mut args = env::args().skip(1);
    let command = args.next().ok_or_else(usage)?;
    let mut database = None;
    let mut store_root = None;
    let mut busy_timeout_ms = 5_000_u64;
    let mut pretty = false;
    let mut job_id = None;
    let mut attempt_id = None;
    let mut workspace_id = None;
    let mut event_limit = DEFAULT_INSPECTION_EVENT_LIMIT;
    let mut job_limit = DEFAULT_WORKSPACE_INSPECTION_JOB_LIMIT;
    let mut include_detail = false;
    let mut since_ms = 0_u64;
    let mut cutoff_ms = None;
    let mut sample_limit = None;

    while let Some(argument) = args.next() {
        match argument.as_str() {
            "--database" => database = Some(PathBuf::from(require_value(&mut args, "--database")?)),
            "--store-root" => {
                store_root = Some(PathBuf::from(require_value(&mut args, "--store-root")?))
            }
            "--busy-timeout-ms" => {
                busy_timeout_ms = require_value(&mut args, "--busy-timeout-ms")?
                    .parse()
                    .map_err(|_| "--busy-timeout-ms must be an integer".to_string())?;
            }
            "--pretty" => pretty = true,
            "--job-id" => job_id = Some(require_value(&mut args, "--job-id")?),
            "--attempt-id" => attempt_id = Some(require_value(&mut args, "--attempt-id")?),
            "--workspace-id" => workspace_id = Some(require_value(&mut args, "--workspace-id")?),
            "--event-limit" => {
                event_limit = require_value(&mut args, "--event-limit")?
                    .parse()
                    .map_err(|_| "--event-limit must be an integer".to_string())?;
            }
            "--include-detail" => include_detail = true,
            "--job-limit" => {
                job_limit = require_value(&mut args, "--job-limit")?
                    .parse()
                    .map_err(|_| "--job-limit must be an integer".to_string())?;
            }
            "--since-ms" => {
                since_ms = require_value(&mut args, "--since-ms")?
                    .parse()
                    .map_err(|_| "--since-ms must be an integer".to_string())?;
            }
            "--cutoff-ms" => {
                cutoff_ms = Some(
                    require_value(&mut args, "--cutoff-ms")?
                        .parse::<u64>()
                        .map_err(|_| "--cutoff-ms must be a non-negative integer".to_string())?,
                );
            }
            "--sample-limit" => {
                sample_limit = Some(
                    require_value(&mut args, "--sample-limit")?
                        .parse::<u32>()
                        .map_err(|_| "--sample-limit must be an integer".to_string())?,
                );
            }
            "--help" | "-h" => return Err(usage()),
            _ => return Err(format!("unknown argument: {argument}\n{}", usage())),
        }
    }

    let database = database.ok_or_else(usage)?;
    if command != "registry-archive" && (cutoff_ms.is_some() || sample_limit.is_some()) {
        return Err("--cutoff-ms and --sample-limit are archive-only flags".to_string());
    }
    let value = match command.as_str() {
        "registry" => {
            if job_id.is_some()
                || workspace_id.is_some()
                || store_root.is_some()
                || since_ms != 0
                || job_limit != DEFAULT_WORKSPACE_INSPECTION_JOB_LIMIT
                || event_limit != DEFAULT_INSPECTION_EVENT_LIMIT
                || include_detail
            {
                return Err(
                    "--job-id, --workspace-id, --store-root, --since-ms, --job-limit, --event-limit, and --include-detail are not valid for registry"
                        .to_string(),
                );
            }
            serde_json::to_value(
                inspect_registry(
                    &RuntimeInspectionConfig {
                        db_path: database.clone(),
                        busy_timeout_ms,
                    },
                    attempt_id.as_deref(),
                )
                .map_err(|error| error.to_string())?,
            )
        }
        "registry-archive" => {
            if job_id.is_some()
                || attempt_id.is_some()
                || workspace_id.is_some()
                || store_root.is_some()
                || since_ms != 0
                || job_limit != DEFAULT_WORKSPACE_INSPECTION_JOB_LIMIT
                || event_limit != DEFAULT_INSPECTION_EVENT_LIMIT
                || include_detail
            {
                return Err("filters other than --cutoff-ms and --sample-limit are not valid for registry-archive".to_string());
            }
            let cutoff_ms = cutoff_ms
                .ok_or_else(|| "registry-archive requires --cutoff-ms".to_string())?;
            let sample_limit = sample_limit.unwrap_or(20);
            if sample_limit > MAX_ARCHIVE_SAMPLE_LIMIT {
                return Err(format!(
                    "--sample-limit must be <= {MAX_ARCHIVE_SAMPLE_LIMIT}"
                ));
            }
            serde_json::to_value(
                inspect_registry_archive(
                    &RuntimeInspectionConfig {
                        db_path: database.clone(),
                        busy_timeout_ms,
                    },
                    cutoff_ms,
                    sample_limit,
                )
                .map_err(|error| error.to_string())?,
            )
        }
        "registry-status" => {
            if job_id.is_some()
                || attempt_id.is_some()
                || workspace_id.is_some()
                || store_root.is_some()
                || since_ms != 0
                || event_limit != DEFAULT_INSPECTION_EVENT_LIMIT
                || include_detail
            {
                return Err("filters other than --job-limit are not valid for registry-status".to_string());
            }
            serde_json::to_value(
                inspect_registry_status(
                    &RuntimeInspectionConfig {
                        db_path: database.clone(),
                        busy_timeout_ms,
                    },
                    job_limit,
                )
                .map_err(|error| error.to_string())?,
            )
        }
        "registry-markers" => {
            if job_id.is_some()
                || attempt_id.is_some()
                || store_root.is_some()
                || since_ms != 0
                || job_limit != DEFAULT_WORKSPACE_INSPECTION_JOB_LIMIT
                || event_limit != DEFAULT_INSPECTION_EVENT_LIMIT
                || include_detail
            {
                return Err(
                    "filters other than --workspace-id are not valid for registry-markers"
                        .to_string(),
                );
            }
            serde_json::to_value(
                inspect_registry_markers(
                    &RuntimeInspectionConfig {
                        db_path: database.clone(),
                        busy_timeout_ms,
                    },
                    workspace_id.as_deref(),
                )
                .map_err(|error| error.to_string())?,
            )
        }
        "registry-activity" => {
            if job_id.is_some()
                || attempt_id.is_some()
                || workspace_id.is_some()
                || store_root.is_some()
                || since_ms != 0
                || job_limit != DEFAULT_WORKSPACE_INSPECTION_JOB_LIMIT
                || event_limit != DEFAULT_INSPECTION_EVENT_LIMIT
                || include_detail
            {
                return Err("filters are not valid for registry-activity".to_string());
            }
            serde_json::to_value(
                inspect_registry_activity(&RuntimeInspectionConfig {
                    db_path: database.clone(),
                    busy_timeout_ms,
                })
                .map_err(|error| error.to_string())?,
            )
        }
        "registry-workspace" => {
            if job_id.is_some()
                || attempt_id.is_some()
                || store_root.is_some()
                || since_ms != 0
                || job_limit != DEFAULT_WORKSPACE_INSPECTION_JOB_LIMIT
                || event_limit != DEFAULT_INSPECTION_EVENT_LIMIT
                || include_detail
            {
                return Err(
                    "--job-id, --attempt-id, --store-root, --since-ms, --job-limit, --event-limit, and --include-detail are not valid for registry-workspace"
                        .to_string(),
                );
            }
            let workspace_id = workspace_id
                .ok_or_else(|| "registry-workspace requires --workspace-id".to_string())?;
            serde_json::to_value(
                inspect_registry_workspace_activity(
                    &RuntimeInspectionConfig {
                        db_path: database.clone(),
                        busy_timeout_ms,
                    },
                    &workspace_id,
                )
                .map_err(|error| error.to_string())?,
            )
        }
        "job" => {
            if attempt_id.is_some()
                || since_ms != 0
                || store_root.is_some()
                || workspace_id.is_some()
                || job_limit != DEFAULT_WORKSPACE_INSPECTION_JOB_LIMIT
            {
                return Err(
                    "--attempt-id, --since-ms, --store-root, --workspace-id, and --job-limit are not valid for job"
                        .to_string(),
                );
            }
            let job_id = job_id.ok_or_else(|| "job requires --job-id".to_string())?;
            serde_json::to_value(
                inspect_job(
                    &RuntimeInspectionConfig {
                        db_path: database.clone(),
                        busy_timeout_ms,
                    },
                    &job_id,
                    event_limit,
                    include_detail,
                )
                .map_err(|error| error.to_string())?,
            )
        }
        "summary" => {
            if job_id.is_some()
                || attempt_id.is_some()
                || workspace_id.is_some()
                || store_root.is_some()
                || job_limit != DEFAULT_WORKSPACE_INSPECTION_JOB_LIMIT
                || event_limit != DEFAULT_INSPECTION_EVENT_LIMIT
                || include_detail
            {
                return Err(
                    "--job-id, --attempt-id, --workspace-id, --store-root, --job-limit, --event-limit, and --include-detail are not valid for summary"
                        .to_string(),
                );
            }
            serde_json::to_value(
                summarize_experience(
                    &RuntimeInspectionConfig {
                        db_path: database.clone(),
                        busy_timeout_ms,
                    },
                    since_ms,
                )
                .map_err(|error| error.to_string())?,
            )
        }
        "workspace" => {
            if job_id.is_some()
                || attempt_id.is_some()
                || since_ms != 0
                || event_limit != DEFAULT_INSPECTION_EVENT_LIMIT
                || include_detail
            {
                return Err(
                    "--job-id, --attempt-id, --since-ms, --event-limit, and --include-detail are not valid for workspace"
                        .to_string(),
                );
            }
            let workspace_id = workspace_id
                .ok_or_else(|| "workspace requires --workspace-id".to_string())?;
            let store_root = store_root
                .ok_or_else(|| "workspace requires --store-root".to_string())?;
            serde_json::to_value(
                inspect_workspace(
                    &RuntimeWorkspaceInspectionConfig {
                        db_path: database.clone(),
                        store_root,
                        busy_timeout_ms,
                    },
                    &workspace_id,
                    job_limit,
                )
                .map_err(|error| error.to_string())?,
            )
        }
        _ => return Err(usage()),
    }
    .map_err(|error| format!("cannot serialize Runtime inspection: {error}"))?;

    let output = if pretty {
        serde_json::to_string_pretty(&value)
    } else {
        serde_json::to_string(&value)
    }
    .map_err(|error| format!("cannot serialize Runtime inspection: {error}"))?;
    println!("{output}");
    Ok(())
}

fn require_value(args: &mut impl Iterator<Item = String>, flag: &str) -> Result<String, String> {
    args.next()
        .ok_or_else(|| format!("{flag} requires a value"))
}

fn usage() -> String {
    format!(
        "usage:\n  ordivon-runtime-inspect registry --database ABSOLUTE_PATH [--attempt-id ID] [--busy-timeout-ms N] [--pretty]\n  ordivon-runtime-inspect registry-archive --database ABSOLUTE_PATH --cutoff-ms UNIX_MS [--sample-limit N<=100] [--busy-timeout-ms N] [--pretty]\n  ordivon-runtime-inspect registry-status --database ABSOLUTE_PATH [--job-limit N] [--busy-timeout-ms N] [--pretty]\n  ordivon-runtime-inspect registry-markers --database ABSOLUTE_PATH [--workspace-id ID] [--busy-timeout-ms N] [--pretty]\n  ordivon-runtime-inspect registry-activity --database ABSOLUTE_PATH [--busy-timeout-ms N] [--pretty]\n  ordivon-runtime-inspect registry-workspace --database ABSOLUTE_PATH --workspace-id ID [--busy-timeout-ms N] [--pretty]\n  ordivon-runtime-inspect job --database ABSOLUTE_PATH --job-id ID [--event-limit N<= {MAX_INSPECTION_EVENT_LIMIT}] [--include-detail] [--busy-timeout-ms N] [--pretty]\n  ordivon-runtime-inspect workspace --database ABSOLUTE_PATH --store-root ABSOLUTE_PATH --workspace-id ID [--job-limit N<= {MAX_WORKSPACE_INSPECTION_JOB_LIMIT}] [--busy-timeout-ms N] [--pretty]\n  ordivon-runtime-inspect summary --database ABSOLUTE_PATH [--since-ms UNIX_MS] [--busy-timeout-ms N] [--pretty]"
    )
}
