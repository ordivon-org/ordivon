from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".agents" / "skills" / "research-capability-routing" / "scripts" / "route.py"
PROFILE = ROOT / ".agents" / "skills" / "research-capability-routing" / "references" / "research-capability-routing-r1.json"
SCHEMA = ROOT / ".agents" / "skills" / "research-capability-routing" / "references" / "research-capability-routing-r1.schema.json"
INDEX = ROOT / "profiles" / "research" / "capability-index" / "research-capability-index-r1.json"
INDEX_SCHEMA = ROOT / "profiles" / "research" / "capability-index" / "research-capability-index-r1.schema.json"
GATEWAY_GENERATOR = ROOT / "services" / "gateway" / "packaging" / "generate_research_routes.py"


def _load_router():
    spec = importlib.util.spec_from_file_location("research_capability_route", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ResearchCapabilityRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.R = _load_router()

    def test_profile_validates_with_mature_check_jsonschema_provider(self) -> None:
        validator = shutil.which("check-jsonschema") or "/root/.local/bin/check-jsonschema"
        self.assertTrue(Path(validator).is_file(), "check-jsonschema provider must be available for source qualification")
        proc = subprocess.run([validator, "--schemafile", str(SCHEMA), str(PROFILE)], text=True, capture_output=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_profile_is_non_authoritative_and_routes_explicit_problem_classes(self) -> None:
        profile = json.loads(PROFILE.read_text(encoding="utf-8"))
        self.assertEqual(profile["truthRole"], "task-routing-profile-not-scientific-or-execution-authority")
        self.assertIn("scholarly.discovery", profile["problemClasses"])
        self.assertIn("data.analytical-query", profile["problemClasses"])
        self.assertIn("workflow.scientific-dag", profile["problemClasses"])
        self.assertIn("workflow.durable-process", profile["problemClasses"])
        self.assertIn("execution.physical", profile["problemClasses"])

    def test_scientific_dag_temporal_and_runtime_are_distinct(self) -> None:
        r = self.R
        dag = r.resolve(r.RouteRequest(problem_class="workflow.scientific-dag"), observations={"study-data-plane": {"state": "available", "bindings": {"workflow.scientific-dag": "Snakemake"}}})
        durable = r.resolve(r.RouteRequest(problem_class="workflow.durable-process"), observations={"temporal": {"state": "available"}})
        physical = r.resolve(r.RouteRequest(problem_class="execution.physical"), observations={"runtime.linux": {"state": "available"}})
        self.assertEqual(dag["selectedRoute"]["providerClass"], "snakemake")
        self.assertEqual(durable["selectedRoute"]["providerClass"], "temporal")
        self.assertEqual(physical["selectedRoute"]["providerClass"], "ordivon-runtime")
        self.assertNotEqual(dag["selectedRoute"]["providerClass"], durable["selectedRoute"]["providerClass"] )

    def test_scholarly_discovery_prefers_specialized_skill_not_generic_agent(self) -> None:
        r = self.R
        d = r.resolve(r.RouteRequest(problem_class="scholarly.discovery"), observations={"skill:paper-lookup": {"state": "available", "bindingRef": "codex-user/paper-lookup"}})
        self.assertEqual(d["standing"], "ROUTED")
        self.assertEqual(d["selectedRoute"]["providerClass"], "skill")
        self.assertEqual(d["selectedRoute"]["providerRef"], "paper-lookup")
        self.assertEqual(d["executionAuthority"], "selected-owner-or-provider")
        self.assertEqual(d["completionAuthority"], "study-or-owning-domain")

    def test_required_specialist_unavailable_returns_hold_not_generic_agent_fallback(self) -> None:
        r = self.R
        d = r.resolve(r.RouteRequest(problem_class="document.scholarly-pdf-parse"), observations={"provider:grobid": {"state": "unavailable", "reason": "not admitted"}})
        self.assertEqual(d["standing"], "HOLD_NO_READY_ROUTE")
        self.assertIsNone(d["selectedRoute"] )
        self.assertNotIn("generic-agent", [row["routeId"] for row in d["candidates"]])

    def test_literature_review_dependency_gap_is_preserved(self) -> None:
        r = self.R
        d = r.resolve(r.RouteRequest(problem_class="scholarly.synthesis"), observations={"skill:literature-review": {"state": "degraded", "reason": "required dependencies paper-writing/general-writing unavailable"}})
        self.assertEqual(d["standing"], "HOLD_NO_READY_ROUTE")
        self.assertIn("required dependencies", d["candidates"][0]["availability"]["reason"] )

    def test_research_data_plane_uses_owner_binding_instead_of_hardcoded_cli_truth(self) -> None:
        r = self.R
        for problem, expected in [
            ("data.analytical-query", "DuckDB"),
            ("data.dataframe-transform", "Polars LazyFrame"),
            ("data.normalization", "Apache Arrow"),
            ("data.analytical-storage", "Apache Parquet"),
        ]:
            d = r.resolve(r.RouteRequest(problem_class=problem), observations={"study-data-plane": {"state": "available", "bindings": {problem: expected}}})
            self.assertEqual(d["standing"], "ROUTED")
            self.assertEqual(d["selectedRoute"]["bindingAuthority"], "research-study-owner")
            self.assertEqual(d["selectedRoute"]["providerBinding"], expected)
            self.assertFalse(d["selectedRoute"]["scientificSemanticAuthority"] )

    def test_owner_binding_can_preserve_multi_provider_validation_set(self) -> None:
        r = self.R
        providers = ["Arrow schema", "Pandera", "JSON Schema", "method-native validators"]
        d = r.resolve(r.RouteRequest(problem_class="data.validation"), observations={"study-data-plane": {"state": "available", "bindings": {"data.validation": providers}}})
        self.assertEqual(d["standing"], "ROUTED")
        self.assertEqual(d["selectedRoute"]["providerBinding"], providers)
        self.assertFalse(d["selectedRoute"]["scientificSemanticAuthority"])

    def test_skill_route_requires_skill_owner_observation(self) -> None:
        r = self.R
        d = r.resolve(r.RouteRequest(problem_class="statistics.analysis"), observations={})
        self.assertEqual(d["standing"], "HOLD_CURRENTNESS_REQUIRED")
        self.assertEqual(d["candidates"][0]["availability"]["state"], "unknown")

    def test_explicit_caller_bound_provider_can_be_used_but_does_not_authorize(self) -> None:
        r = self.R
        d = r.resolve(r.RouteRequest(problem_class="document.rich-parse"), observations={"provider:docling": {"state": "caller_bound", "bindingRef": "connector:docling"}}, caller_available=("provider:docling",))
        self.assertEqual(d["standing"], "ROUTED")
        self.assertFalse(d["authorizationEstablished"] )
        self.assertIn("does not grant authority", " ".join(d["nonClaims"]))

    def test_route_plan_digests_are_deterministic_and_currentness_bound(self) -> None:
        r = self.R
        request = r.RouteRequest(problem_class="scholarly.discovery")
        obs = {"skill:paper-lookup": {"state": "available", "bindingRef": "codex-user/paper-lookup"}}
        a = r.resolve(request, observations=obs)
        b = r.resolve(request, observations=obs)
        self.assertEqual(a, b)
        for key in ("profileDigest", "requestDigest", "observationDigest", "planDigest"):
            self.assertRegex(a[key], r"^sha256:[0-9a-f]{64}$")
        changed = r.resolve(request, observations={"skill:paper-lookup": {"state": "available", "bindingRef": "codex-user/paper-lookup", "reason": "fresh owner observation"}})
        self.assertEqual(a["profileDigest"], changed["profileDigest"])
        self.assertNotEqual(a["observationDigest"], changed["observationDigest"])
        self.assertNotEqual(a["planDigest"], changed["planDigest"])

    def test_unknown_problem_class_fails_closed(self) -> None:
        r = self.R
        with self.assertRaises(ValueError):
            r.resolve(r.RouteRequest(problem_class="made.up.research.action"), observations={})

    def test_route_emits_invocation_and_verification_without_execution(self) -> None:
        r = self.R
        d = r.resolve(r.RouteRequest(problem_class="citation.identity"), observations={"skill:citation-management": {"state": "available", "bindingRef": "codex-user/citation-management"}})
        route = d["selectedRoute"]
        self.assertIn("invocation", route)
        self.assertIn("verification", route)
        self.assertFalse(d["executed"] )
        self.assertFalse(d["domainCompletionEstablished"] )

    def test_capability_index_validates_and_refs_only_declared_problem_classes(self) -> None:
        validator = shutil.which("check-jsonschema") or "/root/.local/bin/check-jsonschema"
        self.assertTrue(Path(validator).is_file())
        proc = subprocess.run(
            [validator, "--schemafile", str(INDEX_SCHEMA), str(INDEX)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        profile = json.loads(PROFILE.read_text(encoding="utf-8"))
        declared = set(profile["problemClasses"])
        capabilities = [row["capability"] for row in index["capabilities"]]
        self.assertEqual(len(capabilities), len(set(capabilities)))
        for row in index["capabilities"]:
            self.assertLessEqual(set(row["routeProblemClasses"]), declared)
            self.assertNotIn("preferredSkills", row)

    def test_gateway_research_projection_is_generated_from_index_and_routing_profile(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(GATEWAY_GENERATOR), "--check"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("PASS_RESEARCH_GATEWAY_PROJECTION_CURRENT", proc.stdout)


if __name__ == "__main__":
    unittest.main()
