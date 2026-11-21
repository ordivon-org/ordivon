mod intent;
mod realization;

use super::super::{AttemptState, JobResolution, RuntimeReleaseEffectBinding, RuntimeResult};
use super::receipt::{inspect_receipt, ReleaseReceiptProjection};

/// The stable Release contract API; each behavior is defined by its owner.
pub(crate) struct ReleaseStateContract;

impl ReleaseStateContract {
    pub(crate) fn inspect_receipt(
        binding: &RuntimeReleaseEffectBinding,
        job_resolution: Option<JobResolution>,
        attempt_state: Option<AttemptState>,
    ) -> RuntimeResult<ReleaseReceiptProjection> {
        inspect_receipt(binding, job_resolution, attempt_state)
    }
}
