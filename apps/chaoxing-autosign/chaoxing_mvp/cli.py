from __future__ import annotations

import tempfile
from pathlib import Path

from .adapters import ConsoleNotifier, FakeAcceptedSubmission, FakeDiscovery, FakeSession
from .engine import AutoSignEngine
from .ledger import ActivityLedger
from .models import Activity, ActivityIdentity, ActivityKind, CourseIdentity
from .ports import Ports


def build_demo() -> AutoSignEngine:
    account = "demo-account"
    course = CourseIdentity(
        account_id=account,
        course_id="course-1",
        class_id="class-a",
        course_name="Demo Course",
    )
    normal = Activity(
        identity=ActivityIdentity(
            account_id=account,
            course_id=course.course_id,
            class_id=course.class_id,
            activity_id="normal-1",
            acquisition_surface="synthetic",
        ),
        kind=ActivityKind.NORMAL,
    )
    qr = Activity(
        identity=ActivityIdentity(
            account_id=account,
            course_id=course.course_id,
            class_id=course.class_id,
            activity_id="qr-1",
            acquisition_surface="synthetic",
        ),
        kind=ActivityKind.QR_REQUIRED,
        verification_requirements=("user-supplied-qr",),
    )
    db_path = Path(tempfile.gettempdir()) / "chaoxing-autosign-mvp-demo.sqlite3"
    if db_path.exists():
        db_path.unlink()
    ledger = ActivityLedger(db_path)
    ports = Ports(
        session=FakeSession(account),
        discovery=FakeDiscovery([course], {course.key: [normal, qr]}),
        submission=FakeAcceptedSubmission(),
        notifier=ConsoleNotifier(),
    )
    return AutoSignEngine(ports, ledger)


def main() -> None:
    engine = build_demo()
    stats = engine.scan_once()
    print(stats)


if __name__ == "__main__":
    main()
