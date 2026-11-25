//! Mature pool owns allocation, wait queue, validation and bounded capacity.
//! This tiny lease is only the domain-specific terminality fence.
use crate::NoteError;
use deadpool_postgres::{Manager, ManagerConfig, Object, Pool, RecyclingMethod, Runtime};
use std::{path::Path, time::Duration};
use tokio_postgres::{Client, Config, NoTls};

#[derive(Debug, Clone, Copy)]
pub struct PoolLimits {
    pub max_size: usize,
    pub wait: Duration,
}
impl Default for PoolLimits {
    fn default() -> Self {
        Self {
            max_size: 4,
            wait: Duration::from_secs(5),
        }
    }
}

pub(crate) fn local_pool(
    socket: &Path,
    port: u16,
    user: &str,
    database: &str,
    limits: PoolLimits,
) -> Result<Pool, NoteError> {
    if !socket.is_absolute()
        || port == 0
        || user.is_empty()
        || database.is_empty()
        || limits.max_size == 0
        || limits.wait.is_zero()
    {
        return Err(NoteError::PoolConfig);
    }
    let mut config = Config::new();
    config
        .host_path(socket)
        .port(port)
        .user(user)
        .dbname(database)
        .application_name("ordivon-web-note-candidate")
        .connect_timeout(Duration::from_secs(5));
    let manager = Manager::from_config(
        config,
        NoTls,
        ManagerConfig {
            recycling_method: RecyclingMethod::Clean,
        },
    );
    Pool::builder(manager)
        .max_size(limits.max_size)
        .runtime(Runtime::Tokio1)
        .wait_timeout(Some(limits.wait))
        .create_timeout(Some(Duration::from_secs(5)))
        .recycle_timeout(Some(Duration::from_secs(5)))
        .build()
        .map_err(|_| NoteError::PoolConfig)
}

/// Default disposition is discard. Drop is synchronous even when the caller
/// future is cancelled. Object::take removes the object from the pool;
/// ClientWrapper's Drop aborts its native driver.
pub(crate) struct Lease {
    object: Option<Object>,
    reusable: bool,
}
impl Lease {
    pub fn new(object: Object) -> Self {
        Self {
            object: Some(object),
            reusable: false,
        }
    }
    pub fn client(&mut self) -> &mut Client {
        self.object.as_mut().expect("live lease")
    }
    pub fn reusable(&mut self) {
        self.reusable = true
    }
}
impl Drop for Lease {
    fn drop(&mut self) {
        if !self.reusable
            && let Some(object) = self.object.take()
        {
            drop(Object::take(object));
        }
    }
}
