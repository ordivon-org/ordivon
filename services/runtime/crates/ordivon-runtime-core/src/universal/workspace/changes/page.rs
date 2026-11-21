//! Stable ordered Git change-page selection with whole-set checksum.
use super::{
    BinaryHeap, UniversalExecError, UniversalExecErrorCode, WorkspaceChangeCursor,
    WorkspaceChangeEntry, WorkspaceChangeKind, WorkspaceChangePageRequest,
};
use super::{Digest, Sha256};
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
    pub(super) fn observe(&mut self, encoded: &[u8]) {
        let digest = Sha256::digest(encoded);
        let mut bytes = [0_u8; 32];
        bytes.copy_from_slice(&digest);
        for (target, value) in self.xor.iter_mut().zip(bytes.iter()) {
            *target ^= *value;
        }
        for (index, chunk) in bytes.as_chunks::<8>().0.iter().enumerate() {
            self.sums[index] = self.sums[index].wrapping_add(u64::from_be_bytes(*chunk));
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

pub(super) struct ChangePageCollector {
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
    pub(super) fn new(request: &WorkspaceChangePageRequest) -> Result<Self, UniversalExecError> {
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

    pub(super) fn observe(
        &mut self,
        entry: WorkspaceChangeEntry,
    ) -> Result<(), UniversalExecError> {
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

    pub(super) fn finish(
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

pub(super) struct WorkspaceChangePageSelection {
    pub(super) change_set_digest: String,
    pub(super) entries: Vec<WorkspaceChangeEntry>,
    pub(super) entry_bytes: u64,
    pub(super) total_entries: u64,
    pub(super) remaining_entries: u64,
    pub(super) complete: bool,
    pub(super) next_cursor: Option<WorkspaceChangeCursor>,
}
impl ChangePageCollector {
    pub(super) fn observed_digest(&self) -> String {
        self.accumulator.digest()
    }
}
