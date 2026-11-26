//! Owner-local persistence fence for an already admitted Effect. This is
//! deliberately NOT a public authorization, digest verification or HTTP API.
mod authority;
mod domain;
mod grant_identity;
mod grants;
mod observation;
mod postconditions;
mod rows;
mod transaction;
mod writes;
pub use authority::{ApprovalWrite, GrantRevocation, PendingOutcome};
pub use domain::{EffectError, EffectOperation, EffectOutcome, EffectRequest, GrantFence};
pub use grant_identity::{GrantCreate, GrantObservation, GrantSnapshot, PreparedGrant};
pub use rows::{EffectReceipt, PendingApproval};

pub use observation::{ApprovalView, AuthorityObservation, RevocationObservation};
