"""Portable Python-view controls; independent JS/CLI behavior is native integration."""

import hashlib
import sys
from io import BytesIO
from types import SimpleNamespace

from warcio import archiveiterator

from scripts import artifact_web_archive as warc


def test_python_view_does_not_mutate_import_path_or_read_all_payload(tmp_path, monkeypatch):
    payload = b"x" * (2 * 1024 * 1024 + 19)
    reads = []

    class BoundedStream(BytesIO):
        def read(self, size=-1):
            assert 0 < size <= 1024 * 1024
            reads.append(size)
            return super().read(size)

    record = SimpleNamespace(
        rec_type="response",
        rec_headers=SimpleNamespace(get_header=lambda key: key),
        http_headers=None,
        content_stream=lambda: BoundedStream(payload),
    )
    monkeypatch.setattr(archiveiterator, "ArchiveIterator", lambda _: [record])
    path = tmp_path / "fixture.warc"
    path.write_bytes(b"fixture")
    before = tuple(sys.path)
    rows, error = warc.py_view(path)
    assert tuple(sys.path) == before
    assert error is None
    assert rows[0]["payloadSha256"] == hashlib.sha256(payload).hexdigest()
    assert len(reads) >= 4
