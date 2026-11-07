"""Read-only attention change projection over canonical Host owner rows.

No duplicated event ledger, subscription ranking, or scheduler state.
"""

ATTENTION_DELTA_SQL = """
        WITH relevant AS (
            SELECT ws.change_sequence, 'work_snapshot'::text AS event_kind,
                   ws.work_ref::text AS source_ref, ws.revision::text AS context_ref,
                   true AS followed_work, false AS followed_space, false AS followed_topic,
                   false AS mentioned, false AS replied_to_me, false AS own_participation,
                   false AS own_coordination_intent, 'work'::text AS navigation_kind,
                   ws.work_ref::text AS navigation_ref
            FROM work_snapshots ws
            WHERE ws.change_sequence > %(after_sequence)s AND ws.change_sequence <= %(high)s
              AND EXISTS (
                SELECT 1 FROM subscriptions s
                WHERE s.actor_ref=%(actor_ref)s AND s.target_kind='work'
                  AND s.target_ref=ws.work_ref AND ws.change_sequence > s.change_sequence
              )
            UNION ALL
            SELECT wr.change_sequence, 'work_relation',
                   wr.source_work_ref || ':' || wr.relation || ':' || wr.target_work_ref,
                   wr.relation,
                   true, false, false, false, false, false, false, 'work',
                   CASE WHEN EXISTS (
                     SELECT 1 FROM subscriptions s WHERE s.actor_ref=%(actor_ref)s
                       AND s.target_kind='work' AND s.target_ref=wr.source_work_ref
                       AND wr.change_sequence>s.change_sequence
                   ) THEN wr.source_work_ref ELSE wr.target_work_ref END
            FROM work_relations wr
            WHERE wr.change_sequence > %(after_sequence)s AND wr.change_sequence <= %(high)s
              AND EXISTS (
                SELECT 1 FROM subscriptions s
                WHERE s.actor_ref=%(actor_ref)s AND s.target_kind='work'
                  AND s.target_ref IN (wr.source_work_ref,wr.target_work_ref)
                  AND wr.change_sequence > s.change_sequence
              )
            UNION ALL
            SELECT t.change_sequence, 'topic_change', t.topic_ref, t.space_ref,
                   false,
                   EXISTS (SELECT 1 FROM subscriptions s WHERE s.actor_ref=%(actor_ref)s
                     AND s.target_kind='space' AND s.target_ref=t.space_ref
                     AND t.change_sequence>s.change_sequence),
                   EXISTS (SELECT 1 FROM subscriptions s WHERE s.actor_ref=%(actor_ref)s
                     AND s.target_kind='topic' AND s.target_ref=t.topic_ref
                     AND t.change_sequence>s.change_sequence),
                   false, false, false, false, 'topic', t.topic_ref
            FROM topics t
            WHERE t.change_sequence > %(after_sequence)s AND t.change_sequence <= %(high)s
              AND EXISTS (
                SELECT 1 FROM subscriptions s
                WHERE s.actor_ref=%(actor_ref)s
                  AND ((s.target_kind='topic' AND s.target_ref=t.topic_ref)
                    OR (s.target_kind='space' AND s.target_ref=t.space_ref))
                  AND t.change_sequence > s.change_sequence
              )
            UNION ALL
            SELECT mc.change_sequence, 'message', mc.message_ref, mc.topic_ref,
                   false, bool_or(mc.followed_space), bool_or(mc.followed_topic),
                   bool_or(mc.mentioned), bool_or(mc.replied_to_me),
                   false, false, 'topic', mc.topic_ref
            FROM (
                SELECT m.change_sequence,m.message_ref,m.topic_ref,
                       false AS followed_space,true AS followed_topic,
                       false AS mentioned,false AS replied_to_me
                FROM subscriptions s
                JOIN messages m ON m.topic_ref=s.target_ref
                WHERE s.actor_ref=%(actor_ref)s AND s.target_kind='topic'
                  AND m.change_sequence > %(after_sequence)s AND m.change_sequence <= %(high)s
                  AND m.change_sequence > s.change_sequence
                UNION ALL
                SELECT m.change_sequence,m.message_ref,m.topic_ref,
                       true,false,false,false
                FROM subscriptions s
                JOIN messages m ON m.space_ref=s.target_ref
                WHERE s.actor_ref=%(actor_ref)s AND s.target_kind='space'
                  AND m.change_sequence > %(after_sequence)s AND m.change_sequence <= %(high)s
                  AND m.change_sequence > s.change_sequence
                UNION ALL
                SELECT m.change_sequence,m.message_ref,m.topic_ref,
                       false,false,true,false
                FROM message_relations mr
                JOIN messages m ON m.message_ref=mr.source_message_ref
                WHERE mr.relation='mentions' AND mr.target_ref=%(actor_ref)s
                  AND m.change_sequence > %(after_sequence)s AND m.change_sequence <= %(high)s
                UNION ALL
                SELECT m.change_sequence,m.message_ref,m.topic_ref,
                       false,false,false,true
                FROM messages parent
                JOIN message_relations reply
                  ON reply.target_ref=parent.message_ref AND reply.relation='reply_to'
                JOIN messages m ON m.message_ref=reply.source_message_ref
                WHERE parent.author_actor_ref=%(actor_ref)s
                  AND m.change_sequence > %(after_sequence)s AND m.change_sequence <= %(high)s
            ) mc
            GROUP BY mc.change_sequence,mc.message_ref,mc.topic_ref
            UNION ALL
            SELECT mr.change_sequence, 'message_relation',
                   mr.source_message_ref || ':' || mr.relation || ':' || mr.target_ref, mr.relation,
                   false,
                   EXISTS (SELECT 1 FROM subscriptions s WHERE s.actor_ref=%(actor_ref)s
                     AND s.target_kind='space' AND s.target_ref=source_message.space_ref
                     AND mr.change_sequence>s.change_sequence),
                   EXISTS (SELECT 1 FROM subscriptions s WHERE s.actor_ref=%(actor_ref)s
                     AND s.target_kind='topic' AND s.target_ref=source_message.topic_ref
                     AND mr.change_sequence>s.change_sequence),
                   (mr.relation='mentions' AND mr.target_ref=%(actor_ref)s),
                   (mr.relation='reply_to' AND target_message.author_actor_ref=%(actor_ref)s),
                   false, false, 'topic', source_message.topic_ref
            FROM message_relations mr
            JOIN messages source_message ON source_message.message_ref=mr.source_message_ref
            LEFT JOIN messages target_message ON target_message.message_ref=mr.target_ref
            WHERE mr.change_sequence > %(after_sequence)s AND mr.change_sequence <= %(high)s
              AND (
                (mr.relation='mentions' AND mr.target_ref=%(actor_ref)s)
                OR (mr.relation='reply_to' AND target_message.author_actor_ref=%(actor_ref)s)
                OR EXISTS (SELECT 1 FROM subscriptions s WHERE s.actor_ref=%(actor_ref)s
                  AND ((s.target_kind='topic' AND s.target_ref=source_message.topic_ref)
                    OR (s.target_kind='space' AND s.target_ref=source_message.space_ref))
                  AND mr.change_sequence>s.change_sequence)
              )
            UNION ALL
            SELECT p.change_sequence, 'participation_change', p.space_ref || ':' || p.actor_ref,
                   p.standing, false, false, false, false, false, true, false, 'space', p.space_ref
            FROM participations p
            WHERE p.change_sequence > %(after_sequence)s AND p.change_sequence <= %(high)s
              AND p.actor_ref=%(actor_ref)s
            UNION ALL
            SELECT ci.change_sequence, 'coordination_intent', ci.intent_ref, ci.subject_ref,
                   EXISTS (SELECT 1 FROM subscriptions s WHERE s.actor_ref=%(actor_ref)s
                     AND s.target_kind='work' AND s.target_ref=ci.work_ref
                     AND ci.change_sequence>s.change_sequence),
                   EXISTS (SELECT 1 FROM subscriptions s WHERE s.actor_ref=%(actor_ref)s
                     AND s.target_kind='space' AND s.target_ref=ci.space_ref
                     AND ci.change_sequence>s.change_sequence),
                   false, false, false, false, (ci.actor_ref=%(actor_ref)s),
                   CASE WHEN ci.work_ref IS NOT NULL THEN 'work'
                        WHEN ci.space_ref IS NOT NULL THEN 'space' ELSE 'subject' END,
                   COALESCE(ci.work_ref,ci.space_ref,ci.subject_ref)
            FROM coordination_intents ci
            WHERE ci.change_sequence > %(after_sequence)s AND ci.change_sequence <= %(high)s
              AND (
                ci.actor_ref=%(actor_ref)s
                OR (ci.work_ref IS NOT NULL AND EXISTS (
                  SELECT 1 FROM subscriptions s WHERE s.actor_ref=%(actor_ref)s
                    AND s.target_kind='work' AND s.target_ref=ci.work_ref
                    AND ci.change_sequence>s.change_sequence))
                OR (ci.space_ref IS NOT NULL AND EXISTS (
                  SELECT 1 FROM subscriptions s WHERE s.actor_ref=%(actor_ref)s
                    AND s.target_kind='space' AND s.target_ref=ci.space_ref
                    AND ci.change_sequence>s.change_sequence))
              )
        )
        SELECT change_sequence,event_kind,source_ref,context_ref,followed_work,followed_space,
               followed_topic,mentioned,replied_to_me,own_participation,own_coordination_intent,
               navigation_kind,navigation_ref
        FROM relevant
        ORDER BY change_sequence,event_kind,source_ref
        LIMIT %(limit)s
        """
