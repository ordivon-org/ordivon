"""Finite source and artifact identity obligations plus aggregate-consumer negatives."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from hosted_runner_acceptance import select_artifacts, qualify, WORKFLOW_PATH, PRODUCTS, MAX_ARCHIVE

REPO = "example/game"
RUN_ID = 42
SOURCE = "a" * 40


def fixture():
    repo = {"id": 17, "full_name": REPO}
    run = dict(id=RUN_ID, repository=repo.copy(), head_repository=repo.copy(), path=WORKFLOW_PATH,
               head_branch="main", event="push", status="completed", conclusion="success", head_sha=SOURCE)
    entries = [
        dict(id=100 + i, name=f"ordivon-game-{short}-preview-{SOURCE}", expired=False,
             digest="sha256:" + "b" * 64, size_in_bytes=1000,
             workflow_run=dict(id=RUN_ID, repository_id=17, head_repository_id=17,
                               head_branch="main", head_sha=SOURCE))
        for i, short in enumerate(PRODUCTS)
    ]
    return run, dict(total_count=2, artifacts=entries)


def replace(obj, path, value):
    for part in path[:-1]:
        obj = obj[part]
    obj[path[-1]] = value


class HostedRun(unittest.TestCase):
    def test_exact_positive_and_permutation(self):
        run, artifacts = fixture()
        plan = select_artifacts(run, artifacts, REPO, RUN_ID)
        self.assertEqual(set(plan["artifacts"]), set(PRODUCTS.values()))
        artifacts["artifacts"].reverse()
        self.assertEqual(select_artifacts(run, artifacts, REPO, RUN_ID), plan)

    def test_finite_run_identity_axis(self):
        for path, bad in (
            (("id",), 43), (("id",), 42.0), (("repository", "full_name"), "other/repo"),
            (("head_repository", "id"), 18), (("head_repository", "full_name"), "fork/repo"),
            (("path",), ".github/workflows/other.yml"), (("head_branch",), "feature"),
            (("event",), "pull_request"), (("status",), "in_progress"),
            (("conclusion",), "failure"), (("head_sha",), "0"),
        ):
            with self.subTest(path=path, value=bad):
                run, collection = fixture()
                replace(run, path, bad)
                with self.assertRaises(ValueError):
                    select_artifacts(run, collection, REPO, RUN_ID)

    def test_finite_artifact_axis_for_both_products(self):
        cases = (
            (("id",), 0), (("id",), True), (("name",), "unexpected"),
            (("expired",), True), (("expired",), 0), (("size_in_bytes",), 0),
            (("size_in_bytes",), MAX_ARCHIVE + 1), (("digest",), "sha256:bad"),
            (("workflow_run", "id"), 43), (("workflow_run", "repository_id"), 18),
            (("workflow_run", "head_repository_id"), 18),
            (("workflow_run", "head_branch"), "fork"), (("workflow_run", "head_sha"), "c" * 40),
        )
        for index in range(2):
            for path, bad in cases:
                with self.subTest(product=index, path=path, value=bad):
                    run, collection = fixture()
                    replace(collection["artifacts"][index], path, bad)
                    with self.assertRaises(ValueError):
                        select_artifacts(run, collection, REPO, RUN_ID)

    def test_inventory_and_duplicate_axes(self):
        for fault in ("missing", "extra", "duplicate_id", "duplicate_product", "count", "float_count"):
            with self.subTest(fault=fault):
                run, collection = fixture()
                items = collection["artifacts"]
                if fault == "missing":
                    items.pop()
                elif fault == "extra":
                    items.append(copy.deepcopy(items[0]))
                elif fault == "duplicate_id":
                    items[1]["id"] = items[0]["id"]
                elif fault == "duplicate_product":
                    items[1]["name"] = items[0]["name"]
                elif fault == "float_count":
                    collection["total_count"] = 2.0
                else:
                    collection["total_count"] = 3
                with self.assertRaises(ValueError):
                    select_artifacts(run, collection, REPO, RUN_ID)

    def test_no_partial_success_or_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp)
            run, collection = fixture()
            (stage / "run.json").write_text(json.dumps(run))
            (stage / "artifacts.json").write_text(json.dumps(collection))
            def receipt(path, sha, source, product):
                return dict(status="PASS", product=product, outer_sha256=sha, source_commit=source)
            with patch.dict(os.environ, {"GH_TOKEN": "present"}, clear=True):
                with patch("hosted_runner_acceptance.consume") as consume:
                    with self.assertRaisesRegex(ValueError, "API token"):
                        qualify(stage, REPO, RUN_ID)
                    consume.assert_not_called()
            with patch.dict(os.environ, {}, clear=True):
                with patch("hosted_runner_acceptance.consume", side_effect=receipt) as consume:
                    self.assertEqual(qualify(stage, REPO, RUN_ID)["status"], "PASS")
                    self.assertEqual(consume.call_count, 2)
                def bad_second(path, sha, source, product):
                    result = receipt(path, sha, source, product)
                    if product == "room-encounter":
                        result["outer_sha256"] = "c" * 64
                    return result
                with patch("hosted_runner_acceptance.consume", side_effect=bad_second) as consume:
                    with self.assertRaisesRegex(ValueError, "child receipt differs"):
                        qualify(stage, REPO, RUN_ID)
                    self.assertEqual(consume.call_count, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
