# Age-driven backup transition

The existing daily full timer remains authoritative until an explicit owner
cutover. The installed transition utility defaults to read-only planning.
It consumes the native repo1 inventory and does not maintain a second database
or schedule. Full age is measured by completed backup calendar date in
Asia/Shanghai; a full is selected at seven days, a differential at three days
if none exists in the generation, otherwise an incremental.

The candidate transition uses a separately reviewed systemd drop-in replacing
only ExecStart (retain the native check, identity, timer and priorities):

```ini
[Service]
ExecStart=
ExecStart=/usr/local/bin/ordivon-pgbackrest-transition --execute-until=<explicit-offset-deadline>
```

Do not install the example literally. An owner sets a bounded deadline within
14 days, confirms adequate capacity, excludes competing manual backup/expiry
writers, and monitors the daily service. Expiry is disabled for each transition
backup. An elapsed deadline fails visibly rather than silently reverting to
an expiring full. The existing service is not modified by this change.
Reconcile partial native outcomes using pgBackRest info before retrying.

Admission is conservative, not a reservation. The preflight and native lock
are distinct, and a postcondition detects inventory drift, not an atomic
cross-command fence. Successful native creation is not content verification,
restore qualification or retirement permission. Keep all existing recovery
roots until a real calendar window, explicit native expiry plan, independent
fault domain, consumer recovery and owner release have been qualified.
No automatic reduction of retention or deletion is provided.
