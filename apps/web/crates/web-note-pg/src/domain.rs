//! Owner-local persistence contract. The existing application supplies an
//! admitted Principal; no authentication or authorization is performed here.
use serde::Serialize;
use uuid::Uuid;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum NoteState {
    Draft,
    Published,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Note {
    pub note_id: String,
    pub principal_id: String,
    pub content: String,
    pub state: NoteState,
    pub created_at: i64,
    pub published_at: Option<i64>,
}

fn draft(note_id: Uuid, principal: &str, content: &str, now: i64) -> Note {
    Note {
        note_id: note_id.to_string(),
        principal_id: principal.to_owned(),
        content: content.to_owned(),
        state: NoteState::Draft,
        created_at: now,
        published_at: None,
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct Audit {
    pub event_id: String,
    pub principal_id: Option<String>,
    pub event_type: String,
    pub object_type: Option<String>,
    pub object_id: Option<String>,
    pub detail_json: String,
    pub created_at: i64,
}

impl Audit {
    fn for_note(event_id: Uuid, note: &Note) -> Self {
        Self {
            event_id: event_id.to_string(),
            principal_id: Some(note.principal_id.clone()),
            event_type: "canary.note.created".into(),
            object_type: Some("canary-note".into()),
            object_id: Some(note.note_id.clone()),
            detail_json: "{}".into(),
            created_at: note.created_at,
        }
    }
}

pub(crate) fn representable(principal: &str, content: &str, now: i64) -> bool {
    !principal.contains('\0')
        && !content.contains('\0')
        && (-9_007_199_254_740_991..=9_007_199_254_740_991).contains(&now)
}

// Immutable operation coordinates, allocated synchronously by the caller.
// Restoring these coordinates does not authorize, execute or retry an operation.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PreparedNote {
    pub(crate) note: Note,
    pub(crate) audit: Audit,
}
impl PreparedNote {
    pub fn new(principal: &str, content: &str, now: i64) -> Result<Self, crate::NoteError> {
        Self::restore(Uuid::new_v4(), Uuid::new_v4(), principal, content, now)
    }
    pub fn restore(
        note_id: Uuid,
        event_id: Uuid,
        principal: &str,
        content: &str,
        now: i64,
    ) -> Result<Self, crate::NoteError> {
        if !representable(principal, content, now) {
            return Err(crate::NoteError::Unrepresentable);
        }
        let note = draft(note_id, principal, content, now);
        let audit = Audit::for_note(event_id, &note);
        Ok(Self { note, audit })
    }
    pub fn note_id(&self) -> &str {
        &self.note.note_id
    }
    pub fn event_id(&self) -> &str {
        &self.audit.event_id
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum NoteObservation {
    // Exact original creation projection, not a claim about every later state.
    Exact(Note),
    // No matching rows in this snapshot, NOT proof of noncommit.
    Unobserved,
    // At least one coordinate exists but exact creation evidence differs.
    Mismatch,
}
