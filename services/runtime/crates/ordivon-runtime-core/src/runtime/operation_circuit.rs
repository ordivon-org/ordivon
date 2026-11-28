//! Existing immutable execution circuit: typed request identity -> original SubmitRequest.
//! Domain families are composed independently; no extra persisted state or authority engine.
use super::SubmitRequest;
///
/// R08 intentionally reuses the already-enforced `SubmitRequest`/`RuntimeExecutionPlan` truth
/// instead of creating a second persisted execution schema. The compiler composes one new
/// ordinary admission only after exact replay and R07 authority compilation have already run.
/// Reduced and trusted immutable-input admission are the second and third strangler slices;
/// credential-bound trusted admission is the fourth. Runtime release remains on its dedicated
/// reconciliable effect path rather than being folded into this effect-opaque execution circuit.
#[derive(Debug)]
pub(crate) struct ExecutionCircuit {
    submit: SubmitRequest,
}

impl ExecutionCircuit {
    pub(crate) fn into_submit_request(self) -> SubmitRequest {
        self.submit
    }
}

pub(crate) struct OperationCircuitCompiler;

mod credential;
mod immutable;
mod ordinary;
#[cfg(test)]
mod tests;
