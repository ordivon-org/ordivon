//! Original stable ResourceScheduling/WorkspaceAccess/NodeResources API.
//! Separate caller contracts, workspace lease conflicts, native OS supply.
mod node_supply;
mod request;
mod workspace_access;
pub use node_supply::NodeResources;
pub use request::{ResourceRequest, ResourceScheduling};
pub use workspace_access::WorkspaceAccess;
