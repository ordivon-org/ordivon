SELECT jsonb_build_object(
  'run', to_jsonb(r),
  'events', COALESCE(
    (
      SELECT jsonb_agg(
        jsonb_build_object(
          'event_id', e.event_id,
          'execution_id', e.execution_id,
          'legacy_attempt_id', e.legacy_attempt_id,
          'sequence', e.sequence,
          'event_type', e.event_type,
          'origin', e.origin,
          'previous_state', e.previous_state,
          'new_state', e.new_state,
          'reason_code', e.reason_code,
          'data_digest', e.data_digest,
          'observed_at', e.observed_at
        )
        ORDER BY e.sequence
      )
      FROM r5c.execution_events e
      WHERE e.execution_id = r.execution_id
    ),
    '[]'::jsonb
  ),
  'artifacts', COALESCE(
    (
      SELECT jsonb_agg(
        jsonb_build_object(
          'artifact_id', a.artifact_id,
          'execution_id', a.execution_id,
          'legacy_attempt_id', a.legacy_attempt_id,
          'kind', a.kind,
          'relative_path', a.relative_path,
          'digest', a.digest,
          'media_type', a.media_type,
          'byte_length', a.byte_length,
          'truncated', a.truncated,
          'created_at', a.created_at
        )
        ORDER BY a.kind, a.relative_path, a.artifact_id
      )
      FROM r5c.execution_artifacts a
      WHERE a.execution_id = r.execution_id
    ),
    '[]'::jsonb
  )
)::text
FROM r5c.execution_runs r
ORDER BY r.created_at, r.execution_id;
