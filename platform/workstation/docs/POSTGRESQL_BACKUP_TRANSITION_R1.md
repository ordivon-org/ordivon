# PostgreSQL backup transition R1

Standing: candidate; not an installed policy or authorization to expire production data.

## Problem and authority

The shared PostgreSQL service currently uses the daily full pgBackRest backup and seven-full retention. PostgreSQL owns database truth; pgBackRest owns manifests, archive retrieval, recovery and expiry. systemd owns scheduling, not recovery standing. Preserve every required recovery point and externally declared retention root. No second backup engine, registry, or scheduler.

## Logic and capability

| Logic | Native capability | Obligation |
|---|---|---|
| Repository identity | pgBackRest info | Bind repository, database epoch, labels and observation cut |
| Schedule | Existing systemd timer | Separate requested time, actual execution and completed backup |
| Backup production | pgBackRest full/diff/incr | Candidate weekly full, midweek diff, daily incr otherwise |
| Recovery closure | Native manifests and WAL | Required daily points, continuous timeline-aware archive, consumer semantics |
| Expiry plan | Native expire dry-run | Exact labels and archive range; no effect from planning |
| Recovery | PostgreSQL restore/PITR | Promote, then check actual domain witnesses |
| Lifecycle | Native expire | Same-cut maintenance fence, explicit recovery and owner qualification |

## Migration

1. Observe actual completed backup inventory, repository identity and available capacity. Keep the existing full-count seven and archive coverage during transition. Do not lower retention with the first new backup. Do not treat a successful command or missed-timer activation as a daily recovery point.
2. Qualify production change of schedule separately from retention. The proposed weekly full, midweek differential and remaining daily incremental schedule is a candidate, not installed configuration. Reuse existing timer/native backup; avoid parallel catch-up activations and explicitly qualify delayed/missed full backup and actual backup kind. Monitor native completion, not wall-clock intent.
3. Establish at least seven actual required daily points with real Host, Runtime and Temporal restore witnesses, an independently checked WAL interval and measured RPO/RTO. Verify exact backup status and required WAL access separately. For off-device protection use actual independent failure domain evidence, not path count.
4. Compare count-based and time-based native expiry (14 days is a candidate, not a selected production policy), including extra full backups, missed scheduled days, disk/IO costs and dependency closure. Do not infer that two full generations imply seven daily points. Do not indefinitely disable expiry.
5. Under the natural owner's coordinated repository/backup/maintenance fence, re-observe exact current manifests and policy, inspect native dry-run plan and reject any plan intersecting recovery/consumer/forensic roots. Only then authorize actual native expiry. Verify exact post-effect inventory and restore capability separately. Never manually delete archive segments or backup paths.
6. Maintain old carrier and rollback/recovery obligations until the production consumers have accepted. A rollback of configuration cannot undo an expired backup.

## Evidence and tests

2026-11-26 production metadata observation: seven full labels Nov 20–26. Native dry-run count 2 planned expiry of five; count 7 and time 14 planned no expiry. Before/after manifest and archive-range observations equal. No actual production expiry executed. This is a bounded cut, not a guarantee for future time-based or count-based policy.

R17–R19 opt-in native tests in this directory's sibling tests: explicit backup validity vs exit status; required WAL missing/retrieved; nine backups, native deferred expiry and two alternative plans; seven exact restored points and continuous same-timeline WAL retrieval. Private fixtures only; not a production seven-calendar-day, full-cluster, RTO or failure-domain proof.

Run the native tests only on an authorized isolated operator workspace with PostgreSQL and pgBackRest installed. Normal unprivileged discovery skips these native fixtures by default. Preserve existing safety smoke tests and independent restore semantics.

References:
- https://pgbackrest.org/configuration.html
- https://pgbackrest.org/command.html
- https://www.postgresql.org/docs/18/continuous-archiving.html
- https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html
