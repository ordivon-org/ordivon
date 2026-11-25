-- Native psql, autocommit only (no --single-transaction).
-- An independently approved DBA applies this to the exact active Runtime
-- schema, not an unqualified import, public, or Harness. No data rewrites.
\set ON_ERROR_STOP on
SELECT pg_catalog.set_config('search_path', pg_catalog.format('%I', :'runtime_schema'), false) AS path \gset
SELECT COALESCE(current_schema() = :'runtime_schema'
  AND :'runtime_schema' ~ '^[A-Za-z][A-Za-z0-9_]{0,62}$'
  AND :'runtime_schema' NOT IN ('public','information_schema')
  AND left(:'runtime_schema',3) <> 'pg_'
  AND :'source_sha256' ~ '^[0-9a-fA-F]{64}$'
  AND NOT pg_is_in_recovery(), false) AS scope_ok \gset
\if :scope_ok
\else
DO $$ BEGIN RAISE EXCEPTION 'Refusing unqualified Runtime Artifact index scope'; END $$;
\endif

-- Bind the same source/physical epoch predicate as writer_authority.rs.
-- A post-PITR or historical schema may not self-promote via this migration.
WITH physical AS (
  SELECT system_identifier::text AS system_id,
    (SELECT timeline_id FROM pg_control_checkpoint()) AS timeline,
    left(pg_walfile_name(pg_current_wal_lsn()),8) AS wal_timeline
  FROM pg_control_system()
)
SELECT COALESCE(timeline > 0
  AND wal_timeline = upper(lpad(to_hex(timeline),8,'0'))
  AND EXISTS(SELECT 1 FROM _stage_control WHERE id='source'
    AND state='QUALIFIED_WRITER' AND source_sha256=:'source_sha256' AND promotion_allowed)
  AND EXISTS(SELECT 1 FROM _stage_control WHERE id='epoch'
    AND state='QUALIFIED_EPOCH' AND promotion_allowed
    AND source_sha256=encode(sha256(
      convert_to('ordivon-pg-writer-epoch-v1','UTF8') || decode('00','hex')
      || convert_to(:'source_sha256','UTF8') || decode('00','hex')
      || convert_to(system_id,'UTF8') || decode('00','hex')
      || convert_to(timeline::text,'UTF8')), 'hex')),false) AS epoch_ok
FROM physical \gset
\if :epoch_ok
\else
DO $$ BEGIN RAISE EXCEPTION 'Runtime Artifact index source/physical epoch not qualified'; END $$;
\endif

-- The native catalog, not the name alone, is the acceptance authority.
-- Concurrent same-name creation fails safely; do not drop or repair it here.
SELECT EXISTS(SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE n.nspname=current_schema() AND c.relname='idx_artifacts_job') AS already_present \gset
\if :already_present
\else
SELECT format('CREATE INDEX CONCURRENTLY %I ON %I.%I USING btree (%I)',
  'idx_artifacts_job', current_schema(), 'artifacts', 'job_id') \gexec
\endif
SELECT EXISTS(
  SELECT 1 FROM pg_index i
  JOIN pg_class c ON c.oid=i.indexrelid
  JOIN pg_class t ON t.oid=i.indrelid
  JOIN pg_namespace n ON n.oid=t.relnamespace
  JOIN pg_am am ON am.oid=c.relam
  JOIN pg_attribute a ON a.attrelid=t.oid AND a.attname='job_id' AND NOT a.attisdropped
  JOIN pg_opclass opc ON opc.oid=i.indclass[0]
  WHERE n.nspname=current_schema() AND t.relname='artifacts'
    AND c.relnamespace=t.relnamespace AND c.relname='idx_artifacts_job'
    AND c.relkind='i' AND t.relkind='r' AND am.amname='btree'
    AND i.indisvalid AND i.indisready AND i.indislive
    AND NOT i.indisunique AND NOT i.indisprimary AND NOT i.indisexclusion
    AND i.indnkeyatts=1 AND i.indnatts=1 AND i.indkey[0]=a.attnum
    AND i.indpred IS NULL AND i.indexprs IS NULL
    AND i.indcollation[0]=a.attcollation AND i.indoption[0]=0
    AND opc.opcdefault AND opc.opcmethod=am.oid AND opc.opcintype=a.atttypid
) AS exact_index \gset
\if :exact_index
\echo Runtime Artifact Job lookup index qualified
\else
DO $$ BEGIN RAISE EXCEPTION 'Runtime Artifact Job lookup index absent, invalid, or conflicting; operator review required'; END $$;
\endif
