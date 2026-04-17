-- PFIOS Core Completion Migration
-- Target: DuckDB pfios_main.duckdb

-- 1. Update Recommendations Table
ALTER TABLE recommendations ADD COLUMN analysis_id VARCHAR;
ALTER TABLE recommendations ADD COLUMN title VARCHAR DEFAULT 'Financial Intelligence Recommendation';
ALTER TABLE recommendations ADD COLUMN summary TEXT;
ALTER TABLE recommendations ADD COLUMN rationale TEXT;
ALTER TABLE recommendations ADD COLUMN expected_outcome TEXT;
ALTER TABLE recommendations ADD COLUMN outcome_metric_type VARCHAR;
ALTER TABLE recommendations ADD COLUMN outcome_metric_config JSON;
ALTER TABLE recommendations ADD COLUMN priority VARCHAR DEFAULT 'medium';
ALTER TABLE recommendations ADD COLUMN adopted_at TIMESTAMP;
ALTER TABLE recommendations ADD COLUMN due_at TIMESTAMP;
ALTER TABLE recommendations ADD COLUMN expires_at TIMESTAMP;
ALTER TABLE recommendations ADD COLUMN completed_at TIMESTAMP;
ALTER TABLE recommendations ADD COLUMN review_required BOOLEAN DEFAULT TRUE;
ALTER TABLE recommendations ADD COLUMN review_due_at TIMESTAMP;
ALTER TABLE recommendations ADD COLUMN latest_outcome_snapshot_id VARCHAR;
ALTER TABLE recommendations ADD COLUMN archived_at TIMESTAMP;

-- 2. Create Outcome Snapshots Table
CREATE TABLE IF NOT EXISTS outcome_snapshots (
    snapshot_id VARCHAR PRIMARY KEY,
    recommendation_id VARCHAR,
    observed_at TIMESTAMP,
    outcome_state VARCHAR,
    observed_metrics JSON,
    evidence_refs JSON,
    trigger_reason TEXT,
    note TEXT
);

-- 3. Create Review Queue Table
CREATE TABLE IF NOT EXISTS review_queue (
    item_id VARCHAR PRIMARY KEY,
    recommendation_id VARCHAR,
    analysis_id VARCHAR,
    outcome_snapshot_id VARCHAR,
    reason TEXT,
    priority VARCHAR DEFAULT 'medium',
    status VARCHAR DEFAULT 'pending',
    scheduled_at TIMESTAMP,
    created_at TIMESTAMP
);

-- 4. Create Lessons Table (Expansion of review lessons)
CREATE TABLE IF NOT EXISTS lessons (
    lesson_id VARCHAR PRIMARY KEY,
    review_id VARCHAR,
    recommendation_id VARCHAR,
    title VARCHAR,
    body TEXT,
    lesson_type VARCHAR,
    tags JSON,
    confidence DOUBLE,
    source_refs JSON,
    wiki_path VARCHAR,
    created_at TIMESTAMP
);

-- 5. Update Performance Reviews Table
-- DuckDB doesn't support easy RENAME COLUMN/DROP COLUMN for existing tables without recreating.
-- We'll add the new columns and keep the old ones for compatibility for now.
ALTER TABLE performance_reviews ADD COLUMN recommendation_id VARCHAR;
ALTER TABLE performance_reviews ADD COLUMN analysis_id VARCHAR;
ALTER TABLE performance_reviews ADD COLUMN review_type VARCHAR DEFAULT 'performance';
ALTER TABLE performance_reviews ADD COLUMN status VARCHAR DEFAULT 'pending';
ALTER TABLE performance_reviews ADD COLUMN verdict VARCHAR;
ALTER TABLE performance_reviews ADD COLUMN scheduled_at TIMESTAMP;
ALTER TABLE performance_reviews ADD COLUMN started_at TIMESTAMP;
ALTER TABLE performance_reviews ADD COLUMN completed_at TIMESTAMP;
ALTER TABLE performance_reviews ADD COLUMN observed_outcome TEXT;
ALTER TABLE performance_reviews ADD COLUMN variance_summary TEXT;
ALTER TABLE performance_reviews ADD COLUMN cause_tags JSON;
ALTER TABLE performance_reviews ADD COLUMN followup_actions JSON;
ALTER TABLE performance_reviews ADD COLUMN wiki_path VARCHAR;
