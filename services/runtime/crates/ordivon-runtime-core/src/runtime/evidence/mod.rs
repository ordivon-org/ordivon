//! The original Runtime evidence contract, composed from observable effects.
//! Keep the existing consumer API; only private ownership boundaries move.
mod captured_output;
mod errors;
mod resource_receipt;
mod source_observation;
mod terminal;

pub(crate) use source_observation::{
    validate_workspace_source_observation_artifact, SourceObservationRequirement,
};
pub(crate) use terminal::prepare_runner_terminal_from_bundle;

pub(crate) const RESULT_FILE: &str = "result.json";
const REQUEST_FILE: &str = "request.json";
const STDOUT_FILE: &str = "stdout.log";
const STDERR_FILE: &str = "stderr.log";
const WORKSPACE_SOURCE_OBSERVATION_FILE: &str = "workspace-source-observation.json";
