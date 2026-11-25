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

pub(crate) fn draft(principal: &str, content: &str, now: i64) -> Note {
    Note {
        note_id: Uuid::new_v4().to_string(),
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
    pub fn for_note(note: &Note) -> Self {
        Self {
            event_id: Uuid::new_v4().to_string(),
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
