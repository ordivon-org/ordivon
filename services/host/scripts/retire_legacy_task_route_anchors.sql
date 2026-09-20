-- One-time, idempotent data migration for databases that still contain the retired
-- synthetic Board -> Task route-anchor rows. Schema migration 0005 has already
-- materialized the authoritative task_id foreign key before this script is eligible.
BEGIN;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM board_messages
    WHERE client_message_id LIKE 'task-route-anchor-v1:%'
      AND author_label = 'task-routing-anchor-v1'
      AND message_kind = 'note'
      AND topic = 'agent-native-collaboration-routing'
      AND reply_to_client_message_id IS NULL
      AND task_id IS NULL
  ) THEN
    RAISE EXCEPTION 'legacy route anchor without task_id; refuse destructive cleanup';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM board_messages AS child
    JOIN board_messages AS anchor
      ON anchor.client_message_id = child.reply_to_client_message_id
    WHERE anchor.client_message_id LIKE 'task-route-anchor-v1:%'
      AND anchor.author_label = 'task-routing-anchor-v1'
      AND anchor.message_kind = 'note'
      AND anchor.topic = 'agent-native-collaboration-routing'
      AND anchor.reply_to_client_message_id IS NULL
      AND child.task_id IS DISTINCT FROM anchor.task_id
  ) THEN
    RAISE EXCEPTION 'legacy route child disagrees with materialized task_id; refuse destructive cleanup';
  END IF;
END
$$;

WITH anchors AS (
  SELECT client_message_id
  FROM board_messages
  WHERE client_message_id LIKE 'task-route-anchor-v1:%'
    AND author_label = 'task-routing-anchor-v1'
    AND message_kind = 'note'
    AND topic = 'agent-native-collaboration-routing'
    AND reply_to_client_message_id IS NULL
)
UPDATE board_messages AS child
SET reply_to_client_message_id = NULL
FROM anchors
WHERE child.reply_to_client_message_id = anchors.client_message_id;

DELETE FROM board_messages
WHERE client_message_id LIKE 'task-route-anchor-v1:%'
  AND author_label = 'task-routing-anchor-v1'
  AND message_kind = 'note'
  AND topic = 'agent-native-collaboration-routing'
  AND reply_to_client_message_id IS NULL;

COMMIT;
