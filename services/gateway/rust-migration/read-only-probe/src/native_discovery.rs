//! Compose metadata selection with one natural Owner observation in the
//! qualification carrier. No public route, grant, status cache or effect.
use crate::{
    matching::{RuntimeSearchFixture, RuntimeSearchPlan, SearchResult},
    owner_observation::{Observation, observe_runtime},
};
use serde::Serialize;
use std::time::Duration;

#[derive(Serialize)]
pub struct Discovery {
    projection: SearchResult,
    observation: Option<Observation>,
}

pub async fn discover_runtime_fixture(
    fixture: RuntimeSearchFixture,
    endpoint: &str,
    expected_node: &str,
) -> Result<Discovery, &'static str> {
    let plan = RuntimeSearchPlan::new(fixture)?;
    let observation = if plan.requires_observation() {
        Some(observe_runtime(endpoint, expected_node, Duration::from_secs(3), false).await)
    } else {
        None
    };
    let evidence = observation.as_ref().map(|o| match o {
        Observation::Reported { available, .. } => (*available, None),
        Observation::Unobserved { reason } => (false, Some((*reason).to_owned())),
    });
    let projection = plan.project(evidence)?;
    Ok(Discovery {
        projection,
        observation,
    })
}
