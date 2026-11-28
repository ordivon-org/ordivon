mod artifact;
mod contract;
#[cfg(test)]
mod physical_tests;
#[cfg(test)]
mod tests;

pub(crate) use artifact::validate_workspace_source_observation_artifact;
pub(crate) use contract::SourceObservationRequirement;
