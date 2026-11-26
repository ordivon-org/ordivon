//! Reuse the installed verifier; fixed executable and script, bounded stdio.
use serde::Deserialize;
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
pub struct LocalVerifier {
    node: PathBuf,
    script: PathBuf,
    slots: Arc<Semaphore>,
    deadline: Duration,
}
#[derive(Debug)]
pub(super) enum VerifyError {
    Unavailable,
    Protocol,
}
#[derive(Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub(super) enum Reply {
    Options { options: Value },
    Verified { counter: u32 },
    Denied,
}
impl LocalVerifier {
    pub fn new(
        node: &Path,
        script: &Path,
        max_parallel: usize,
        deadline: Duration,
    ) -> std::io::Result<Self> {
        if !node.is_absolute()
            || !script.is_absolute()
            || !(1..=64).contains(&max_parallel)
            || deadline.is_zero()
            || deadline > Duration::from_secs(30)
        {
            return Err(std::io::Error::new(
                std::io::ErrorKind::InvalidInput,
                "verifier config",
            ));
        }
        let node = node.canonicalize()?;
        let script = script.canonicalize()?;
        if !node.is_file() || !script.is_file() {
            return Err(std::io::Error::new(
                std::io::ErrorKind::InvalidInput,
                "verifier files",
            ));
        }
        Ok(Self {
            node,
            script,
            slots: Arc::new(Semaphore::new(max_parallel)),
            deadline,
        })
    }
    pub(super) async fn call(&self, request: Value) -> Result<Reply, VerifyError> {
        let input = serde_json::to_vec(&request).map_err(|_| VerifyError::Protocol)?;
        if input.len() > LIMIT {
            return Err(VerifyError::Protocol);
        }
        let _permit = self
            .slots
            .try_acquire()
            .map_err(|_| VerifyError::Unavailable)?;
        let mut child = Command::new(&self.node)
            .arg(&self.script)
            .env_clear()
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .kill_on_drop(true)
            .spawn()
            .map_err(|_| VerifyError::Unavailable)?;
        let mut stdin = child.stdin.take().ok_or(VerifyError::Protocol)?;
        let stdout = child.stdout.take().ok_or(VerifyError::Protocol)?;
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
                tokio::try_join!(send, receive).map_err(|_| VerifyError::Unavailable)?;
            if bytes.len() > LIMIT {
                return Err(VerifyError::Protocol);
            }
            if !child
                .wait()
                .await
                .map_err(|_| VerifyError::Unavailable)?
                .success()
            {
                return Err(VerifyError::Unavailable);
            }
            serde_json::from_slice(&bytes).map_err(|_| VerifyError::Protocol)
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
                Err(VerifyError::Unavailable)
            }
        }
    }
}
