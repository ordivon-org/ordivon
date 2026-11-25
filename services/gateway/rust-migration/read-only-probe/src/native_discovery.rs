//! Compose metadata selection with one natural Owner observation in the
//! qualification carrier. No public route, grant, status cache or effect.
use crate::{
    matching::{RuntimeSearchFixture, RuntimeSearchPlan, SearchResult},
    owner_observation::{Observation, observe_protected_runtime, observe_runtime},
};
use serde::Serialize;
use std::{path::Path, time::Duration};

#[derive(Serialize)]
pub struct Discovery {
    projection: SearchResult,
    observation: Option<Observation>,
}

pub async fn discover_runtime_fixture(
    fixture: RuntimeSearchFixture,
    endpoint: &str,
    expected_node: &str,
    credential: Option<&Path>,
) -> Result<Discovery, &'static str> {
    let plan = RuntimeSearchPlan::new(fixture)?;
    let observation = if plan.requires_observation() {
        let budget = Duration::from_secs(3);
        Some(match credential {
            Some(path) => {
                observe_protected_runtime(endpoint, expected_node, path, budget, false).await
            }
            None => observe_runtime(endpoint, expected_node, budget, false).await,
        })
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
