use std::collections::HashMap;
use std::sync::{Arc, Mutex, MutexGuard, Weak};

use super::{RuntimeError, RuntimeErrorCode, RuntimeResult};

#[derive(Clone, Debug, Default)]
pub(super) struct WorkspaceLeaseTable {
    leases: Arc<Mutex<HashMap<String, Weak<Mutex<()>>>>>,
}

impl WorkspaceLeaseTable {
    pub(super) fn with_lease<T>(
        &self,
        workspace_id: &str,
        operation: impl FnOnce() -> RuntimeResult<T>,
    ) -> RuntimeResult<T> {
        let lease = {
            let mut leases = self.leases.lock().map_err(|_| {
                RuntimeError::new(
                    RuntimeErrorCode::RegistryUnavailable,
                    "Workspace lease table is poisoned",
                    None,
                    true,
                )
            })?;
            leases.retain(|_, lease| lease.strong_count() > 0);
            if let Some(existing) = leases.get(workspace_id).and_then(Weak::upgrade) {
                existing
            } else {
                let lease = Arc::new(Mutex::new(()));
                leases.insert(workspace_id.to_string(), Arc::downgrade(&lease));
                lease
            }
        };

        let _guard = lease.lock().map_err(|_| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryUnavailable,
                "Workspace lease is poisoned",
                Some("workspaceId"),
                true,
            )
        })?;
        operation()
    }
}

pub(super) fn lock_topology(lock: &Mutex<()>) -> RuntimeResult<MutexGuard<'_, ()>> {
    lock.lock().map_err(|_| {
        RuntimeError::new(
            RuntimeErrorCode::RegistryUnavailable,
            "Workspace topology lock is poisoned",
            None,
            true,
        )
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::mpsc;
    use std::thread;
    use std::time::Duration;

    #[test]
    fn unrelated_workspace_leases_overlap() {
        let leases = WorkspaceLeaseTable::default();
        let (entered_tx, entered_rx) = mpsc::channel();
        let (release_tx, release_rx) = mpsc::channel();

        let leases_a = leases.clone();
        let holder = thread::spawn(move || {
            leases_a
                .with_lease("workspace-a", || {
                    entered_tx.send(()).unwrap();
                    release_rx.recv().unwrap();
                    Ok(())
                })
                .unwrap();
        });
        entered_rx.recv_timeout(Duration::from_secs(1)).unwrap();

        let leases_b = leases.clone();
        let (other_tx, other_rx) = mpsc::channel();
        let other = thread::spawn(move || {
            leases_b
                .with_lease("workspace-b", || {
                    other_tx.send(()).unwrap();
                    Ok(())
                })
                .unwrap();
        });
        other_rx
            .recv_timeout(Duration::from_secs(1))
            .expect("unrelated Workspace lease was serialized behind workspace-a");

        release_tx.send(()).unwrap();
        holder.join().unwrap();
        other.join().unwrap();
    }

    #[test]
    fn same_workspace_lease_serializes() {
        let leases = WorkspaceLeaseTable::default();
        let (entered_tx, entered_rx) = mpsc::channel();
        let (release_tx, release_rx) = mpsc::channel();

        let leases_a = leases.clone();
        let holder = thread::spawn(move || {
            leases_a
                .with_lease("workspace-a", || {
                    entered_tx.send(()).unwrap();
                    release_rx.recv().unwrap();
                    Ok(())
                })
                .unwrap();
        });
        entered_rx.recv_timeout(Duration::from_secs(1)).unwrap();

        let leases_same = leases.clone();
        let (other_tx, other_rx) = mpsc::channel();
        let waiter = thread::spawn(move || {
            leases_same
                .with_lease("workspace-a", || {
                    other_tx.send(()).unwrap();
                    Ok(())
                })
                .unwrap();
        });
        assert!(
            other_rx.recv_timeout(Duration::from_millis(100)).is_err(),
            "same Workspace lease entered concurrently"
        );

        release_tx.send(()).unwrap();
        other_rx.recv_timeout(Duration::from_secs(1)).unwrap();
        holder.join().unwrap();
        waiter.join().unwrap();
    }

    #[test]
    fn dead_workspace_lease_entries_are_reconstructible() {
        let leases = WorkspaceLeaseTable::default();
        leases.with_lease("workspace-a", || Ok(())).unwrap();
        leases.with_lease("workspace-b", || Ok(())).unwrap();
        let table = leases.leases.lock().unwrap();
        assert_eq!(table.len(), 1);
        assert!(table.contains_key("workspace-b"));
    }
}
