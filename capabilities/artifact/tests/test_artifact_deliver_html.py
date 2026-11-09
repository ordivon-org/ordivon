"""Outcome-first local HTML delivery: an actual document consumed by real browsers."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from scripts import artifact_agent_surface as surface
from scripts import artifact_deliver_html as html


def test_order_rejects_missing_source_without_delivery() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        destination = root / "product.html"
        result = html.deliver(root / "not-present.md", destination)
        assert result["status"] == "FAIL"
        assert not destination.exists()
        assert not destination.with_suffix(".delivery.json").exists()


def test_non_html_destination_and_invalid_language_are_rejected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        src = root / "source.md"
        src.write_text("# Document\n")
        assert html.deliver(src, root / "product.docx")["status"] == "FAIL"
        assert html.deliver(src, root / "product.html", language="bad&tag")["status"] == "FAIL"


def test_offline_check_rejects_missing_sidecar_or_relative_link() -> None:
    p = html.OfflineResourceCheck()
    p.feed(
        '<main><img src="not-copied.png"><link rel="stylesheet" href="styles.css">'
        '<a href="../missing.html">Broken local page</a></main>'
    )
    assert len(p.problems) == 3
    good = html.OfflineResourceCheck()
    good.feed('<main><img src="data:image/png;base64,iVBORw0KGgo="><a href="#top">Top</a></main>')
    assert good.problems == []


def test_browser_and_axe_must_both_pass_even_when_provider_says_pass() -> None:
    def result(axe_status: str, firefox: str = "PASS") -> dict:
        return {
            "status": "PASS",
            "digestBound": True,
            "verifierOutput": {"browsers": {
                "chromium": {"status": "PASS", "accessibility": {"status": axe_status}},
                "firefox": {"status": firefox},
            }},
        }

    assert html.accepted_browser(result("PASS"))
    assert not html.accepted_browser(result("FAIL"))
    assert not html.accepted_browser(result("PASS", "NOT_INSTALLED"))
    candidate = result("PASS")
    candidate["digestBound"] = False
    assert not html.accepted_browser(candidate)


def test_agent_builds_actual_delivery_plan_without_a_profile_or_validator_choice() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "source.md"
        src.write_text("# Goal\n")
        with mock.patch.object(surface, "_plan", return_value={
            "ready": True,
            "blockers": [],
            "plan": {"executable": "native-artifact-python", "args": []},
        }):
            result = surface.execute_surface_action("artifact_deliver_html_propose", {
                "source": str(src),
                "destination": str(Path(tmp) / "result.html"),
            })
        assert result["ready"] is True
        assert result["outcome"] == "offline-html-delivery"
        assert "profileId" not in result
        assert result["plan"]["executable"] == "native-artifact-python"


@pytest.mark.integration
def test_real_pandoc_html_checker_browsers_axe_and_delivery_readback() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "customer-brief.md"
        source.write_text(
            "# Ordivon Outcome\n\nThis is a real, standalone customer deliverable.\n"
            "\n## Acceptance\n\nActual browsers must read the delivered file.\n",
            encoding="utf-8",
        )
        target = root / "delivered" / "outcome.html"
        result = html.deliver(source, target)
        assert result["status"] == "DELIVERED", result
        assert result["acceptance"] == {
            "nuHtmlChecker": "PASS", "chromium": "PASS", "firefox": "PASS",
            "automatedAccessibility": "PASS",
            "actualDeliveryPathReadback": "PASS",
            "offlineResourceReferences": "SELF_CONTAINED",
        }
        assert target.is_file()
        assert "<main>" in target.read_text()
        receipt = json.loads(target.with_suffix(".delivery.json").read_text())
        assert receipt["artifact"] == result["artifact"]
        assert receipt["destination"] == str(target)
        assert html.digest(target) == receipt["artifact"]["sha256"]
        again = html.deliver(source, target)
        assert again["status"] == "DELIVERED"
        assert again["artifact"]["sha256"] == result["artifact"]["sha256"]


@pytest.mark.integration
def test_real_pandoc_publication_preserves_nonmatching_existing_destination() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "brief.md"
        source.write_text("# Real result\n\nHello.\n")
        destination = root / "existing.html"
        destination.write_text("KEEP ORIGINAL FILE")
        result = html.deliver(source, destination)
        assert result["status"] == "FAIL"
        assert "already exists" in result["failures"][0]
        assert destination.read_text() == "KEEP ORIGINAL FILE"
        assert not destination.with_suffix(".delivery.json").exists()
