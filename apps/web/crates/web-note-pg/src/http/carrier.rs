//! Shared bounded JSON process transport; no domain authority.
use serde::de::DeserializeOwned;
use serde_json::Value;
use std::{
    path::{Path, PathBuf},
    process::Stdio,
    sync::Arc,
    time::Duration,
};
use tokio::{
    io::{AsyncReadExt, AsyncWriteExt},
    process::Command,
    sync::Semaphore,
};
const LIMIT: usize = 262144;
#[derive(Clone)]
pub(super) struct JsonCarrier {
    executable: PathBuf,
    script: PathBuf,
    slots: Arc<Semaphore>,
    deadline: Duration,
    path: Option<PathBuf>,
}
#[derive(Debug)]
pub(super) enum CarrierError {
    Unavailable,
    Protocol,
}
impl JsonCarrier {
    pub(super) fn new(
        executable: &Path,
        script: &Path,
        max_parallel: usize,
        deadline: Duration,
    ) -> std::io::Result<Self> {
        if !executable.is_absolute()
            || !script.is_absolute()
            || !(1..=64).contains(&max_parallel)
            || deadline.is_zero()
            || deadline > Duration::from_secs(30)
        {
            return Err(std::io::Error::new(
                std::io::ErrorKind::InvalidInput,
                "carrier config",
            ));
        }
        let executable = executable.canonicalize()?;
        let script = script.canonicalize()?;
        if !executable.is_file() || !script.is_file() {
            return Err(std::io::Error::new(
                std::io::ErrorKind::InvalidInput,
                "carrier files",
            ));
        }
        Ok(Self {
            executable,
            script,
            slots: Arc::new(Semaphore::new(max_parallel)),
            deadline,
            path: None,
        })
    }
    pub(super) fn with_path(mut self, path: &Path) -> std::io::Result<Self> {
        let path = path.canonicalize()?;
        if !path.is_dir() {
            return Err(std::io::Error::new(
                std::io::ErrorKind::InvalidInput,
                "carrier PATH",
            ));
        }
        self.path = Some(path);
        Ok(self)
    }
    pub(super) async fn call<T: DeserializeOwned>(
        &self,
        request: Value,
    ) -> Result<T, CarrierError> {
        let input = serde_json::to_vec(&request).map_err(|_| CarrierError::Protocol)?;
        if input.len() > LIMIT {
            return Err(CarrierError::Protocol);
        }
        let _permit = self
            .slots
            .try_acquire()
            .map_err(|_| CarrierError::Unavailable)?;
        let mut command = Command::new(&self.executable);
        command.arg(&self.script).env_clear();
        if let Some(path) = &self.path {
            command.env("PATH", path);
        }
        let mut child = command
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .kill_on_drop(true)
            .spawn()
            .map_err(|_| CarrierError::Unavailable)?;
        let mut stdin = child.stdin.take().ok_or(CarrierError::Protocol)?;
        let stdout = child.stdout.take().ok_or(CarrierError::Protocol)?;
        let result = tokio::time::timeout(self.deadline, async {
            let send = async move {
                stdin.write_all(&input).await?;
                stdin.shutdown().await
            };
            let receive = async {
                let mut bytes = Vec::new();
                stdout
                    .take((LIMIT + 1) as u64)
                    .read_to_end(&mut bytes)
                    .await?;
                Ok::<_, std::io::Error>(bytes)
            };
            let (_, bytes) =
                tokio::try_join!(send, receive).map_err(|_| CarrierError::Unavailable)?;
            if bytes.len() > LIMIT {
                return Err(CarrierError::Protocol);
            }
            if !child
                .wait()
                .await
                .map_err(|_| CarrierError::Unavailable)?
                .success()
            {
                return Err(CarrierError::Unavailable);
            }
            serde_json::from_slice(&bytes).map_err(|_| CarrierError::Protocol)
        })
        .await;
        match result {
            Ok(Ok(reply)) => Ok(reply),
            Ok(Err(e)) => {
                let _ = child.kill().await;
                Err(e)
            }
            Err(_) => {
                let _ = child.kill().await;
                Err(CarrierError::Unavailable)
            }
        }
    }
}
