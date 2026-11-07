-- ELE project-research projection. Natural-owner Git sources remain authoritative.
-- This schema is not an executable-provider registry or a LEGO admission service.
CREATE SCHEMA IF NOT EXISTS ele;
CREATE TABLE IF NOT EXISTS ele.study_versions (
  study_id text NOT NULL,
  sha256 char(64) NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
  kind text NOT NULL,
  source_path text NOT NULL,
  source_cut char(40) NOT NULL CHECK (source_cut ~ '^[0-9a-f]{40}$'),
  title text NOT NULL,
  content text NOT NULL,
  first_imported_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (study_id,sha256),
  UNIQUE (source_path,sha256)
);
CREATE TABLE IF NOT EXISTS ele.study_sections (
  study_id text NOT NULL,
  sha256 char(64) NOT NULL,
  ordinal integer NOT NULL CHECK (ordinal >= 0),
  heading_level smallint NOT NULL CHECK (heading_level BETWEEN 0 AND 6),
  heading_path text[] NOT NULL,
  heading text NOT NULL,
  body text NOT NULL,
  start_line integer NOT NULL CHECK (start_line >= 0),
  end_line integer NOT NULL CHECK (end_line >= start_line),
  PRIMARY KEY (study_id,sha256,ordinal),
  FOREIGN KEY (study_id,sha256)
    REFERENCES ele.study_versions (study_id,sha256) ON DELETE RESTRICT
);
CREATE TABLE IF NOT EXISTS ele.study_heads (
  study_id text PRIMARY KEY,
  sha256 char(64) NOT NULL,
  source_cut char(40) NOT NULL CHECK (source_cut ~ '^[0-9a-f]{40}$'),
  present boolean NOT NULL DEFAULT true,
  last_imported_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (study_id,sha256)
    REFERENCES ele.study_versions (study_id,sha256) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS ele_study_sections_search
  ON ele.study_sections USING gin (to_tsvector('simple',body));
CREATE OR REPLACE VIEW ele.current_studies AS
  SELECT v.study_id,v.sha256,v.kind,v.source_path,
         h.source_cut AS last_observed_source_cut,v.title,v.content,h.last_imported_at
  FROM ele.study_heads AS h
  JOIN ele.study_versions AS v ON v.study_id=h.study_id AND v.sha256=h.sha256
  WHERE h.present;
