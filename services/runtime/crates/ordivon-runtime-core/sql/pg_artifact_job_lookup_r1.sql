-- Server SQL only. Execute with native psql -X -w -v ON_ERROR_STOP=1
-- in autocommit, under separately approved operator maintenance standing.
-- Supply exact search_path, ordivon.runtime_schema and ordivon.source_sha256
-- as connection/session settings. Never use --single-transaction.
-- The pre/post guards do not hold an epoch lock across the concurrent DDL.
DO $guard$
DECLARE
  expected_schema text := current_setting('ordivon.runtime_schema', true);
  expected_source text := current_setting('ordivon.source_sha256', true);
  actual_system_id text;
  actual_timeline integer;
  wal_timeline text;
BEGIN
  IF NOT COALESCE(current_schema() = expected_schema
      AND expected_schema ~ '^[A-Za-z][A-Za-z0-9_]{0,62}$'
      AND current_schemas(false) = ARRAY[expected_schema::name]
      AND expected_schema NOT IN ('public','information_schema')
      AND left(expected_schema,3) <> 'pg_'
      AND expected_source ~ '^[0-9a-fA-F]{64}$'
      AND NOT pg_is_in_recovery(), false) THEN
    RAISE EXCEPTION 'Refusing unqualified Runtime Artifact index scope';
  END IF;
  -- Never let an absent owner table fall through to another search-path
  -- relation or an implicit temporary schema.
  IF to_regclass('artifacts') IS NULL OR to_regclass('_stage_control') IS NULL
      OR to_regclass('artifacts') IS DISTINCT FROM to_regclass(format('%I.artifacts', expected_schema))
      OR to_regclass('_stage_control') IS DISTINCT FROM to_regclass(format('%I._stage_control', expected_schema)) THEN
    RAISE EXCEPTION 'Runtime Artifact index owner table identity mismatch';
  END IF;
  SELECT system_identifier::text,
    (SELECT timeline_id FROM pg_control_checkpoint()),
    left(pg_walfile_name(pg_current_wal_lsn()),8)
  INTO STRICT actual_system_id, actual_timeline, wal_timeline
  FROM pg_control_system();
  IF NOT COALESCE(actual_timeline > 0
      AND wal_timeline = upper(lpad(to_hex(actual_timeline),8,'0'))
      AND EXISTS(SELECT 1 FROM _stage_control WHERE id='source'
        AND state='QUALIFIED_WRITER' AND source_sha256=expected_source AND promotion_allowed)
      AND EXISTS(SELECT 1 FROM _stage_control WHERE id='epoch'
        AND state='QUALIFIED_EPOCH' AND promotion_allowed
        AND source_sha256=encode(sha256(
          convert_to('ordivon-pg-writer-epoch-v1','UTF8') || decode('00','hex')
          || convert_to(expected_source,'UTF8') || decode('00','hex')
          || convert_to(actual_system_id,'UTF8') || decode('00','hex')
          || convert_to(actual_timeline::text,'UTF8')), 'hex')), false) THEN
    RAISE EXCEPTION 'Runtime Artifact index source/physical epoch not qualified';
  END IF;
END
$guard$;

-- IF NOT EXISTS is only a native idempotent creation primitive. The final
-- catalog check, not its NOTICE or the object's name, decides acceptance.
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_artifacts_job ON artifacts USING btree (job_id);

-- A source/epoch change during the online build must not yield success.
DO $guard$
DECLARE
  expected_schema text := current_setting('ordivon.runtime_schema', true);
  expected_source text := current_setting('ordivon.source_sha256', true);
  actual_system_id text;
  actual_timeline integer;
  wal_timeline text;
BEGIN
  IF NOT COALESCE(current_schema() = expected_schema
      AND expected_schema ~ '^[A-Za-z][A-Za-z0-9_]{0,62}$'
      AND current_schemas(false) = ARRAY[expected_schema::name]
      AND expected_schema NOT IN ('public','information_schema')
      AND left(expected_schema,3) <> 'pg_'
      AND expected_source ~ '^[0-9a-fA-F]{64}$'
      AND NOT pg_is_in_recovery(), false) THEN
    RAISE EXCEPTION 'Refusing unqualified Runtime Artifact index scope';
  END IF;
  -- Never let an absent owner table fall through to another search-path
  -- relation or an implicit temporary schema.
  IF to_regclass('artifacts') IS NULL OR to_regclass('_stage_control') IS NULL
      OR to_regclass('artifacts') IS DISTINCT FROM to_regclass(format('%I.artifacts', expected_schema))
      OR to_regclass('_stage_control') IS DISTINCT FROM to_regclass(format('%I._stage_control', expected_schema)) THEN
    RAISE EXCEPTION 'Runtime Artifact index owner table identity mismatch';
  END IF;
  SELECT system_identifier::text,
    (SELECT timeline_id FROM pg_control_checkpoint()),
    left(pg_walfile_name(pg_current_wal_lsn()),8)
  INTO STRICT actual_system_id, actual_timeline, wal_timeline
  FROM pg_control_system();
  IF NOT COALESCE(actual_timeline > 0
      AND wal_timeline = upper(lpad(to_hex(actual_timeline),8,'0'))
      AND EXISTS(SELECT 1 FROM _stage_control WHERE id='source'
        AND state='QUALIFIED_WRITER' AND source_sha256=expected_source AND promotion_allowed)
      AND EXISTS(SELECT 1 FROM _stage_control WHERE id='epoch'
        AND state='QUALIFIED_EPOCH' AND promotion_allowed
        AND source_sha256=encode(sha256(
          convert_to('ordivon-pg-writer-epoch-v1','UTF8') || decode('00','hex')
          || convert_to(expected_source,'UTF8') || decode('00','hex')
          || convert_to(actual_system_id,'UTF8') || decode('00','hex')
          || convert_to(actual_timeline::text,'UTF8')), 'hex')), false) THEN
    RAISE EXCEPTION 'Runtime Artifact index source/physical epoch not qualified';
  END IF;
END
$guard$;

DO $catalog$
BEGIN
  IF NOT EXISTS(
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
) THEN
    RAISE EXCEPTION 'Runtime Artifact Job lookup index absent, invalid, or conflicting; operator review required';
  END IF;
END
$catalog$;
