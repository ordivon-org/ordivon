pub(crate) fn workspace_diff(
    config: &UniversalExecutorConfig,
    request: &WorkspaceDiffRequest,
) -> Result<WorkspaceDiffResult, UniversalExecError> {
    request.validate_shape()?;
    let record = load_workspace_record(config, &request.workspace_id)?;
    let workspace = Path::new(&record.workspace_path);
    let mut command = Command::new("git");
    command
        .arg("--no-optional-locks")
        .arg("-C")
        .arg(workspace)
        .args(["diff", "HEAD", "--no-ext-diff", "--no-color", "--binary"]);
    let (bytes, truncated) =
        bounded_command_stdout(&mut command, request.max_bytes, &[0], "git diff")?;
    let (diff, bytes) = bounded_utf8(bytes, truncated, "git diff output")?;
    let changes = workspace_change_projection_at(workspace)?;
    Ok(WorkspaceDiffResult {
        workspace_id: request.workspace_id.clone(),
        diff,
        digest: sha256_bytes(&bytes),
        byte_length: bytes.len() as u64,
        truncated,
        changed_paths: changes.changed,
        modified_paths: changes.modified,
        added_paths: changes.added,
        deleted_paths: changes.deleted,
        renamed_paths: changes.renamed,
        untracked_paths: changes.untracked,
    })
}

fn workspace_changed_paths(
    workspace: &Path,
) -> Result<WorkspaceChangeProjection, UniversalExecError> {
    let output = Command::new("git")
        .arg("--no-optional-locks")
        .arg("-C")
        .arg(workspace)
        .args([
            "diff",
            "HEAD",
            "--name-status",
            "-z",
            "--find-renames",
            "--find-copies",
        ])
        .output()
        .map_err(|error| tool_unavailable("git diff --name-status", error))?;
    if !output.status.success() {
        return Err(tool_failed("git diff --name-status", &output.stderr));
    }
    let fields: Vec<&[u8]> = output
        .stdout
        .split(|byte| *byte == 0)
        .filter(|field| !field.is_empty())
        .collect();
    let mut changed = BTreeSet::new();
    let mut modified = BTreeSet::new();
    let mut added = BTreeSet::new();
    let mut deleted = BTreeSet::new();
    let mut renamed = Vec::new();
    let mut index = 0usize;
    while index < fields.len() {
        let status = std::str::from_utf8(fields[index]).map_err(|error| {
            UniversalExecError::new(
                UniversalExecErrorCode::ArtifactNotUtf8,
                format!("git diff status is not UTF-8: {error}"),
                None,
                false,
            )
        })?;
        index += 1;
        let code = status.as_bytes().first().copied().ok_or_else(|| {
            UniversalExecError::new(
                UniversalExecErrorCode::ToolFailed,
                "git diff emitted an empty path status",
                None,
                false,
            )
        })?;
        let path = |raw: &[u8]| -> Result<String, UniversalExecError> {
            String::from_utf8(raw.to_vec()).map_err(|error| {
                UniversalExecError::new(
                    UniversalExecErrorCode::ArtifactNotUtf8,
                    format!("changed Git path is not UTF-8: {error}"),
                    None,
                    false,
                )
            })
        };
        match code {
            b'R' | b'C' => {
                if index + 1 >= fields.len() {
                    return Err(UniversalExecError::new(
                        UniversalExecErrorCode::ToolFailed,
                        "git diff rename/copy record is incomplete",
                        None,
                        false,
                    ));
                }
                let from_path = path(fields[index])?;
                let to_path = path(fields[index + 1])?;
                index += 2;
                if code == b'R' {
                    changed.insert(from_path.clone());
                    changed.insert(to_path.clone());
                    renamed.push(WorkspaceRenamedPath { from_path, to_path });
                } else {
                    changed.insert(to_path.clone());
                    added.insert(to_path);
                }
            }
            b'M' | b'T' | b'U' => {
                if index >= fields.len() {
                    return Err(UniversalExecError::new(
                        UniversalExecErrorCode::ToolFailed,
                        "git diff path record is incomplete",
                        None,
                        false,
                    ));
                }
                let value = path(fields[index])?;
                index += 1;
                changed.insert(value.clone());
                modified.insert(value);
            }
            b'A' => {
                if index >= fields.len() {
                    return Err(UniversalExecError::new(
                        UniversalExecErrorCode::ToolFailed,
                        "git diff added-path record is incomplete",
                        None,
                        false,
                    ));
                }
                let value = path(fields[index])?;
                index += 1;
                changed.insert(value.clone());
                added.insert(value);
            }
            b'D' => {
                if index >= fields.len() {
                    return Err(UniversalExecError::new(
                        UniversalExecErrorCode::ToolFailed,
                        "git diff deleted-path record is incomplete",
                        None,
                        false,
                    ));
                }
                let value = path(fields[index])?;
                index += 1;
                changed.insert(value.clone());
                deleted.insert(value);
            }
            _ => {
                return Err(UniversalExecError::new(
                    UniversalExecErrorCode::ToolFailed,
                    format!("unsupported git diff path status: {status}"),
                    None,
                    false,
                ));
            }
        }
    }
    Ok(WorkspaceChangeProjection {
        changed: changed.into_iter().collect(),
        modified: modified.into_iter().collect(),
        added: added.into_iter().collect(),
        deleted: deleted.into_iter().collect(),
        renamed,
        untracked: Vec::new(),
    })
}

pub(crate) fn workspace_change_projection_at(
    workspace: &Path,
) -> Result<WorkspaceChangeProjection, UniversalExecError> {
    let workspace = canonical_directory(workspace, "workspacePath")?;
    let mut changes = workspace_changed_paths(&workspace)?;
    let output = Command::new("git")
        .arg("--no-optional-locks")
        .arg("-C")
        .arg(&workspace)
        .args(["ls-files", "--others", "--exclude-standard", "-z"])
        .output()
        .map_err(|error| tool_unavailable("git ls-files", error))?;
    if !output.status.success() {
        return Err(tool_failed("git ls-files", &output.stderr));
    }
    for raw in output.stdout.split(|byte| *byte == 0) {
        if raw.is_empty() {
            continue;
        }
        changes
            .untracked
            .push(String::from_utf8(raw.to_vec()).map_err(|error| {
                UniversalExecError::new(
                    UniversalExecErrorCode::ArtifactNotUtf8,
                    format!("untracked Git path is not UTF-8: {error}"),
                    None,
                    false,
                )
            })?);
    }
    Ok(changes)
}

fn read_nul_field<R: BufRead>(
    reader: &mut R,
    context: &str,
) -> Result<Option<Vec<u8>>, UniversalExecError> {
    let max_bytes = usize::try_from(super::MAX_WORKSPACE_IO_BYTES).unwrap_or(usize::MAX);
    let mut field = Vec::new();
    loop {
        let available = reader.fill_buf().map_err(|error| {
            UniversalExecError::new(
                UniversalExecErrorCode::IoError,
                format!("read {context}: {error}"),
                None,
                true,
            )
        })?;
        if available.is_empty() {
            if field.is_empty() {
                return Ok(None);
            }
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::ToolFailed,
                format!("{context} ended before NUL terminator"),
                None,
                false,
            ));
        }
        if let Some(index) = available.iter().position(|byte| *byte == 0) {
            if field.len().saturating_add(index) > max_bytes {
                return Err(UniversalExecError::new(
                    UniversalExecErrorCode::OutputLimitExceeded,
                    format!("{context} field exceeds {max_bytes} bytes"),
                    Some("maxBytes"),
                    false,
                ));
            }
            field.extend_from_slice(&available[..index]);
            reader.consume(index + 1);
            return Ok(Some(field));
        }
        if field.len().saturating_add(available.len()) > max_bytes {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::OutputLimitExceeded,
                format!("{context} field exceeds {max_bytes} bytes"),
                Some("maxBytes"),
                false,
            ));
        }
        let consumed = available.len();
        field.extend_from_slice(available);
        reader.consume(consumed);
    }
}

fn utf8_change_path(raw: Vec<u8>, context: &str) -> Result<String, UniversalExecError> {
    String::from_utf8(raw).map_err(|error| {
        UniversalExecError::new(
            UniversalExecErrorCode::ArtifactNotUtf8,
            format!("{context} is not UTF-8: {error}"),
            None,
            false,
        )
    })
}

fn tracked_change_entry<R: BufRead>(
    reader: &mut R,
) -> Result<Option<WorkspaceChangeEntry>, UniversalExecError> {
    let Some(status) = read_nul_field(reader, "git diff --name-status")? else {
        return Ok(None);
    };
    let status = std::str::from_utf8(&status).map_err(|error| {
        UniversalExecError::new(
            UniversalExecErrorCode::ArtifactNotUtf8,
            format!("git diff status is not UTF-8: {error}"),
            None,
            false,
        )
    })?;
    let code = status.as_bytes().first().copied().ok_or_else(|| {
        UniversalExecError::new(
            UniversalExecErrorCode::ToolFailed,
            "git diff emitted an empty path status",
            None,
            false,
        )
    })?;
    let one_path = |reader: &mut R, kind: WorkspaceChangeKind| {
        let raw = read_nul_field(reader, "git diff path")?.ok_or_else(|| {
            UniversalExecError::new(
                UniversalExecErrorCode::ToolFailed,
                "git diff path record is incomplete",
                None,
                false,
            )
        })?;
        Ok(WorkspaceChangeEntry {
            kind,
            path: utf8_change_path(raw, "changed Git path")?,
        })
    };
    match code {
        b'M' | b'T' | b'U' => one_path(reader, WorkspaceChangeKind::Modified).map(Some),
        b'A' => one_path(reader, WorkspaceChangeKind::Added).map(Some),
        b'D' => one_path(reader, WorkspaceChangeKind::Deleted).map(Some),
        _ => Err(UniversalExecError::new(
            UniversalExecErrorCode::ToolFailed,
            format!("unsupported git diff path status: {status}"),
            None,
            false,
        )),
    }
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
struct ChangeOrderKey {
    path: String,
    kind: WorkspaceChangeKind,
}

impl ChangeOrderKey {
    fn from_entry(entry: &WorkspaceChangeEntry) -> Self {
        Self {
            path: entry.path.clone(),
            kind: entry.kind,
        }
    }

    fn from_cursor(cursor: &WorkspaceChangeCursor) -> Self {
        Self {
            path: cursor.after_path.clone(),
            kind: cursor.after_kind,
        }
    }
}

#[derive(Debug)]
struct ChangeCandidate {
    order_key: ChangeOrderKey,
    encoded: Vec<u8>,
    entry: WorkspaceChangeEntry,
}

impl PartialEq for ChangeCandidate {
    fn eq(&self, other: &Self) -> bool {
        self.order_key == other.order_key && self.encoded == other.encoded
    }
}

impl Eq for ChangeCandidate {}

impl PartialOrd for ChangeCandidate {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for ChangeCandidate {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        self.order_key
            .cmp(&other.order_key)
            .then_with(|| self.encoded.cmp(&other.encoded))
    }
}

#[derive(Default)]
struct ChangeSetAccumulator {
    xor: [u8; 32],
    sums: [u64; 4],
    count: u64,
}

impl ChangeSetAccumulator {
    fn observe(&mut self, encoded: &[u8]) {
        let digest = Sha256::digest(encoded);
        let mut bytes = [0_u8; 32];
        bytes.copy_from_slice(&digest);
        for (target, value) in self.xor.iter_mut().zip(bytes.iter()) {
            *target ^= *value;
        }
        for (index, chunk) in bytes.chunks_exact(8).enumerate() {
            let mut word = [0_u8; 8];
            word.copy_from_slice(chunk);
            self.sums[index] = self.sums[index].wrapping_add(u64::from_be_bytes(word));
        }
        self.count = self.count.saturating_add(1);
    }

    fn digest(&self) -> String {
        let mut digest = Sha256::new();
        digest.update(b"ordivon-workspace-change-set-v1\0");
        digest.update(self.count.to_be_bytes());
        digest.update(self.xor);
        for sum in self.sums {
            digest.update(sum.to_be_bytes());
        }
        format!("sha256:{}", hex::encode(digest.finalize()))
    }
}

struct ChangePageCollector {
    after_key: Option<ChangeOrderKey>,
    after_key_seen: bool,
    limit: usize,
    max_bytes: u64,
    candidates: BinaryHeap<ChangeCandidate>,
    candidate_bytes: u64,
    eligible_count: u64,
    smallest_oversized_key: Option<ChangeOrderKey>,
    accumulator: ChangeSetAccumulator,
}

impl ChangePageCollector {
    fn new(request: &WorkspaceChangePageRequest) -> Result<Self, UniversalExecError> {
        let after_key = request.cursor.as_ref().map(ChangeOrderKey::from_cursor);
        Ok(Self {
            after_key_seen: after_key.is_none(),
            after_key,
            limit: request.limit as usize,
            max_bytes: request.max_bytes,
            candidates: BinaryHeap::new(),
            candidate_bytes: 0,
            eligible_count: 0,
            smallest_oversized_key: None,
            accumulator: ChangeSetAccumulator::default(),
        })
    }

    fn observe(&mut self, entry: WorkspaceChangeEntry) -> Result<(), UniversalExecError> {
        let encoded = serde_json::to_vec(&entry).map_err(|error| {
            UniversalExecError::new(
                UniversalExecErrorCode::ToolFailed,
                format!("cannot encode workspace change entry: {error}"),
                None,
                false,
            )
        })?;
        self.accumulator.observe(&encoded);
        let order_key = ChangeOrderKey::from_entry(&entry);
        if self.after_key.as_ref() == Some(&order_key) {
            self.after_key_seen = true;
        }
        if self
            .after_key
            .as_ref()
            .is_some_and(|after| &order_key <= after)
        {
            return Ok(());
        }
        self.eligible_count = self.eligible_count.saturating_add(1);
        if encoded.len() as u64 > self.max_bytes {
            if self
                .smallest_oversized_key
                .as_ref()
                .is_none_or(|current| &order_key < current)
            {
                self.smallest_oversized_key = Some(order_key);
            }
            return Ok(());
        }
        self.candidate_bytes = self.candidate_bytes.saturating_add(encoded.len() as u64);
        self.candidates.push(ChangeCandidate {
            order_key,
            encoded,
            entry,
        });
        let memory_budget = self.max_bytes.saturating_mul(2);
        while self.candidates.len() > self.limit.saturating_add(1)
            || (self.candidate_bytes > memory_budget && self.candidates.len() > 1)
        {
            if let Some(removed) = self.candidates.pop() {
                self.candidate_bytes = self
                    .candidate_bytes
                    .saturating_sub(removed.encoded.len() as u64);
            }
        }
        Ok(())
    }

    fn finish(
        self,
        cursor: Option<&WorkspaceChangeCursor>,
    ) -> Result<WorkspaceChangePageSelection, UniversalExecError> {
        let total_entries = self.accumulator.count;
        let change_set_digest = self.accumulator.digest();
        if let Some(cursor) = cursor {
            if cursor.change_set_digest != change_set_digest {
                return Err(UniversalExecError::new(
                    UniversalExecErrorCode::WorkspaceStateMismatch,
                    "workspace change set changed since the previous page",
                    Some("cursor.changeSetDigest"),
                    false,
                ));
            }
            if !self.after_key_seen {
                return Err(UniversalExecError::new(
                    UniversalExecErrorCode::WorkspaceStateMismatch,
                    "cursor afterPath/afterKind is not present in the current change set",
                    Some("cursor.afterPath"),
                    false,
                ));
            }
        }
        let mut candidates = self.candidates.into_vec();
        candidates.sort();
        let oversized_boundary = self.smallest_oversized_key;
        let mut entries = Vec::with_capacity(self.limit);
        let mut entry_bytes = 0_u64;
        let mut last_key = None;
        for candidate in candidates {
            if oversized_boundary
                .as_ref()
                .is_some_and(|boundary| &candidate.order_key > boundary)
            {
                break;
            }
            let cost = candidate.encoded.len() as u64 + u64::from(!entries.is_empty());
            if entries.len() >= self.limit || entry_bytes.saturating_add(cost) > self.max_bytes {
                break;
            }
            entry_bytes = entry_bytes.saturating_add(cost);
            last_key = Some(candidate.order_key);
            entries.push(candidate.entry);
        }
        if entries.is_empty() && self.eligible_count > 0 {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::OutputLimitExceeded,
                "the next workspace change entry exceeds maxBytes",
                Some("maxBytes"),
                false,
            ));
        }
        let remaining_entries = self.eligible_count.saturating_sub(entries.len() as u64);
        let complete = remaining_entries == 0;
        let next_cursor = if complete {
            None
        } else {
            let last_key = last_key.ok_or_else(|| {
                UniversalExecError::new(
                    UniversalExecErrorCode::ToolFailed,
                    "change page could not establish a continuation key",
                    None,
                    false,
                )
            })?;
            Some(WorkspaceChangeCursor {
                change_set_digest: change_set_digest.clone(),
                after_path: last_key.path,
                after_kind: last_key.kind,
            })
        };
        Ok(WorkspaceChangePageSelection {
            change_set_digest,
            entries,
            entry_bytes,
            total_entries,
            remaining_entries,
            complete,
            next_cursor,
        })
    }
}

struct WorkspaceChangePageSelection {
    change_set_digest: String,
    entries: Vec<WorkspaceChangeEntry>,
    entry_bytes: u64,
    total_entries: u64,
    remaining_entries: u64,
    complete: bool,
    next_cursor: Option<WorkspaceChangeCursor>,
}

fn scan_tracked_changes(
    workspace: &Path,
    collector: &mut ChangePageCollector,
) -> Result<(), UniversalExecError> {
    let mut command = Command::new("git");
    command
        .arg("--no-optional-locks")
        .arg("-C")
        .arg(workspace)
        .args([
            "diff",
            "HEAD",
            "--name-status",
            "-z",
            "--no-renames",
            "--no-ext-diff",
            "--no-textconv",
        ])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    let mut child = command
        .spawn()
        .map_err(|error| tool_unavailable("git diff --name-status", error))?;
    let stdout = child.stdout.take().ok_or_else(|| {
        UniversalExecError::new(
            UniversalExecErrorCode::ToolFailed,
            "git diff --name-status stdout pipe is unavailable",
            None,
            false,
        )
    })?;
    let stderr = drain_reader_bounded(child.stderr.take().ok_or_else(|| {
        UniversalExecError::new(
            UniversalExecErrorCode::ToolFailed,
            "git diff --name-status stderr pipe is unavailable",
            None,
            false,
        )
    })?);
    let mut reader = BufReader::new(stdout);
    loop {
        let candidate = match tracked_change_entry(&mut reader) {
            Ok(candidate) => candidate,
            Err(error) => {
                let _ = finish_stream_child(child, stderr, "git diff --name-status", true);
                return Err(error);
            }
        };
        let Some(candidate) = candidate else {
            finish_stream_child(child, stderr, "git diff --name-status", false)?;
            return Ok(());
        };
        if let Err(error) = collector.observe(candidate) {
            let _ = finish_stream_child(child, stderr, "git diff --name-status", true);
            return Err(error);
        }
    }
}

fn scan_untracked_changes(
    workspace: &Path,
    collector: &mut ChangePageCollector,
) -> Result<(), UniversalExecError> {
    let mut command = Command::new("git");
    command
        .arg("--no-optional-locks")
        .arg("-C")
        .arg(workspace)
        .args(["ls-files", "--others", "--exclude-standard", "-z"])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    let mut child = command
        .spawn()
        .map_err(|error| tool_unavailable("git ls-files", error))?;
    let stdout = child.stdout.take().ok_or_else(|| {
        UniversalExecError::new(
            UniversalExecErrorCode::ToolFailed,
            "git ls-files stdout pipe is unavailable",
            None,
            false,
        )
    })?;
    let stderr = drain_reader_bounded(child.stderr.take().ok_or_else(|| {
        UniversalExecError::new(
            UniversalExecErrorCode::ToolFailed,
            "git ls-files stderr pipe is unavailable",
            None,
            false,
        )
    })?);
    let mut reader = BufReader::new(stdout);
    loop {
        let raw = match read_nul_field(&mut reader, "git ls-files") {
            Ok(raw) => raw,
            Err(error) => {
                let _ = finish_stream_child(child, stderr, "git ls-files", true);
                return Err(error);
            }
        };
        let Some(raw) = raw else {
            finish_stream_child(child, stderr, "git ls-files", false)?;
            return Ok(());
        };
        let entry = WorkspaceChangeEntry {
            kind: WorkspaceChangeKind::Untracked,
            path: utf8_change_path(raw, "untracked Git path")?,
        };
        if let Err(error) = collector.observe(entry) {
            let _ = finish_stream_child(child, stderr, "git ls-files", true);
            return Err(error);
        }
    }
}

pub fn workspace_changes_page(
    config: &UniversalExecutorConfig,
    request: &WorkspaceChangePageRequest,
) -> Result<WorkspaceChangePageResult, UniversalExecError> {
    request.validate_shape()?;
    let record = load_workspace_record(config, &request.workspace_id)?;
    let workspace = Path::new(&record.workspace_path);
    let mut collector = ChangePageCollector::new(request)?;
    scan_tracked_changes(workspace, &mut collector)?;
    scan_untracked_changes(workspace, &mut collector)?;
    let selection = collector.finish(request.cursor.as_ref())?;

    // A page is one structured change-set observation even though tracked and
    // untracked facts come from separate Git processes. Re-scan only path/kind
    // facts after selection so a concurrent Workspace transition cannot silently
    // splice two realities into one page. This intentionally does not hash file
    // contents; byte-only changes that preserve the same change membership/kind
    // remain valid for this projection.
    let mut verification = ChangePageCollector::new(request)?;
    scan_tracked_changes(workspace, &mut verification)?;
    scan_untracked_changes(workspace, &mut verification)?;
    let verification_digest = verification.accumulator.digest();
    if verification_digest != selection.change_set_digest {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::WorkspaceMutationIncomplete,
            "workspace change set changed while projecting the page",
            Some("workspaceId"),
            true,
        ));
    }

    Ok(WorkspaceChangePageResult {
        workspace_id: request.workspace_id.clone(),
        change_set_digest: selection.change_set_digest,
        entries: selection.entries,
        entry_bytes: selection.entry_bytes,
        total_entries: selection.total_entries,
        remaining_entries: selection.remaining_entries,
        complete: selection.complete,
        next_cursor: selection.next_cursor,
    })
}
