// Fixture subset of WebStore schema, not a production migration.
// Preserve text representations and nullable Audit fields.
pub const SCHEMA: &str = "
CREATE TABLE principals(principal_id TEXT PRIMARY KEY,user_name TEXT NOT NULL UNIQUE,display_name TEXT NOT NULL,created_at BIGINT NOT NULL);
CREATE TABLE canary_notes(note_id TEXT PRIMARY KEY,principal_id TEXT NOT NULL REFERENCES principals(principal_id),content TEXT NOT NULL,state TEXT NOT NULL CHECK(state IN ('DRAFT','PUBLISHED')),created_at BIGINT NOT NULL,published_at BIGINT);
CREATE INDEX canary_notes_principal_created ON canary_notes(principal_id,created_at DESC,note_id ASC);
CREATE TABLE audit_events(event_id TEXT PRIMARY KEY,principal_id TEXT,event_type TEXT NOT NULL,object_type TEXT,object_id TEXT,detail_json TEXT NOT NULL,created_at BIGINT NOT NULL);
CREATE INDEX audit_events_created_note ON audit_events(object_id) WHERE event_type='canary.note.created' AND object_type='canary-note';
INSERT INTO principals VALUES ('p','p','P',1),('q','q','Q',1);
";
