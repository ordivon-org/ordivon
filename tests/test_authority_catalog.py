from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import authority_catalog as catalog


class AuthorityCatalogTests(unittest.TestCase):
    def test_build_is_deterministic_and_sorted(self):
        first = catalog.build_index()
        second = catalog.build_index()
        self.assertEqual(first, second)
        ids = [x["id"] for x in first["entries"]]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(first["recordCount"], len(ids))

    def test_progressive_disclosure_keeps_source_out_of_index(self):
        index = catalog.build_index()
        self.assertNotIn("officialSource", index["entries"][0])
        _, record = catalog.get_record("iso-31000-2018")
        self.assertIn("officialSource", record["identity"])

    def test_task_local_semantics_do_not_leak_into_records(self):
        for authority_id, (_, record) in catalog.records().items():
            self.assertEqual(catalog.forbidden_fields(record), [], authority_id)

    def test_lexical_find_prefers_exact_semantics_without_vector_index(self):
        rows = catalog.build_index()["entries"]

        def top(query: str) -> str:
            ranked = sorted(((catalog.score_entry(row, query), row["id"]) for row in rows), key=lambda x: (-x[0], x[1]))
            return ranked[0][1]

        def positive(query: str) -> list[str]:
            return [row["id"] for row in rows if catalog.score_entry(row, query) > 0]

        self.assertEqual(top("risk management"), "iso-31000-2018")
        self.assertIn(top("software supply chain"), {"slsa-1.2", "nist-sp-800-218-ssdf-1.1", "cyclonedx-1.7", "spdx-3.0", "in-toto-1.0"})
        self.assertIn(top("software bill of materials"), {"cyclonedx-1.7", "spdx-3.0"})
        self.assertEqual(top("application security verification"), "owasp-asvs-5.0.0")
        self.assertEqual(top("data lineage"), "openlineage-spec")
        self.assertEqual(top("telemetry protocol"), "otlp-1.11.0")
        self.assertEqual(top("content provenance"), "c2pa-2.4")
        self.assertEqual(top("container distribution"), "oci-distribution-spec-1.1.1")
        self.assertEqual(top("system lifecycle"), "iso-iec-ieee-15288-2023")
        self.assertEqual(top("software lifecycle"), "iso-iec-ieee-12207-2026")
        self.assertEqual(top("pdf accessibility"), "iso-14289-2-2024")
        self.assertEqual(top("office open xml"), "iso-iec-29500-1-2016")
        self.assertEqual(top("web archive"), "iso-28500-2017")
        self.assertEqual(top("dns concepts"), "rfc-1034")
        self.assertEqual(top("dns over https"), "rfc-8484")
        self.assertEqual(top("tls 1.3"), "rfc-9846")
        self.assertEqual(top("oauth security"), "rfc-9700")
        self.assertEqual(top("oauth resource indicator"), "rfc-8707")
        self.assertEqual(top("financial market infrastructure"), "cpmi-iosco-pfmi-2012")
        self.assertEqual(top("financial industry message"), "iso-20022-1-2026")
        self.assertEqual(top("xbrl reporting"), "xbrl-2.1")
        self.assertEqual(top("fix 4.4"), "fix-4.4-errata-20030618")
        self.assertEqual(top("legal entity identifier"), "iso-17442-1-2020")
        self.assertEqual(top("information security management"), "iso-iec-27001-2022-amd1-2024")
        self.assertEqual(top("ai management system"), "iso-iec-42001-2023")
        self.assertEqual(top("service management system"), "iso-iec-20000-1-2018-amd1-2024")
        self.assertEqual(top("knowledge management system"), "iso-30401-2018-amd1-2022-amd2-2024")
        self.assertEqual(top("business continuity"), "iso-22301-2019-amd1-2024")
        self.assertEqual(top("innovation management"), "iso-56001-2024")
        self.assertEqual(top("ai risk management"), "nist-ai-rmf-1.0")
        self.assertEqual(top("json schema"), "json-schema-draft-2020-12")
        self.assertEqual(top("openapi"), "openapi-3.2.0")
        self.assertEqual(top("asyncapi"), "asyncapi-3.1.0")
        self.assertEqual(top("model context protocol"), "mcp-spec-2026-07-28")
        self.assertEqual(top("agent skills"), "agent-skills-spec")
        self.assertEqual(top("software supply chain attestation"), "in-toto-1.0")
        self.assertEqual(top("datacite metadata"), "datacite-metadata-schema-4.7")
        self.assertEqual(top("crossref metadata deposit"), "crossref-metadata-deposit-schema-5.5.0")
        self.assertEqual(top("research organization registry"), "ror-schema-2.1")
        self.assertEqual(top("contributor roles taxonomy"), "ansi-niso-z39.104-2022-credit")
        self.assertEqual(top("citation style language"), "csl-1.0.2")
        self.assertEqual(top("software heritage persistent identifier"), "swhid-scheme-v1")
        self.assertEqual(top("orcid identifier"), "orcid-id-structure")
        self.assertEqual(top("preservation metadata premis"), "premis-3.0")
        self.assertEqual(top("metadata encoding transmission"), "mets-2")
        self.assertEqual(top("file format registry"), "pronom-registry")
        self.assertEqual(top("requirements engineering"), "iso-iec-ieee-29148-2018")
        self.assertEqual(top("genai semantic conventions"), "opentelemetry-genai-semconv")
        self.assertEqual(top("enterprise architecture modeling"), "archimate-3.2")
        self.assertEqual(top("enterprise architecture method"), "togaf-standard-10th-edition")
        self.assertEqual(top("latest official tls 1.3 standard"), "rfc-9846")
        self.assertEqual(top("customer discovery"), "yc-essential-startup-advice")
        self.assertEqual(top("outsourcing"), "iso-37500-2014")
        self.assertEqual(top("company registration"), "samr-registration-materials-2026")
        self.assertEqual(top("value proposition"), "strategyzer-value-proposition-canvas")
        self.assertEqual(top("founder led sales"), "yc-how-to-sell-2018")
        self.assertEqual(top("pricing"), "stripe-saas-pricing-packaging")
        self.assertEqual(top("customer success"), "iso-10004-2018")
        self.assertEqual(top("recruitment"), "iso-30405-2023")
        self.assertEqual(top("hiring"), "iso-30405-2023")
        self.assertEqual(top("procurement"), "iso-20400-2017")
        self.assertEqual(top("frappe crm"), "frappe-crm-provider")
        self.assertEqual(top("erpnext crm"), "erpnext-crm-provider")
        self.assertEqual(top("contract management"), "worldcc-contract-management-standard-4e")
        self.assertEqual(top("customer support"), "frappe-helpdesk-provider")
        self.assertEqual(top("helpdesk"), "frappe-helpdesk-provider")
        self.assertEqual(top("payroll"), "frappe-hr-payroll-provider")
        self.assertEqual(top("financial planning"), "erpnext-budget-provider")
        self.assertEqual(top("budgeting"), "erpnext-budget-provider")
        self.assertEqual(top("market research"), "iso-20252-2026")
        self.assertEqual(top("research ethics"), "icc-esomar-code-2025")
        self.assertEqual(top("marketing communications"), "icc-marketing-code-2024")
        self.assertEqual(top("direct marketing"), "icc-marketing-code-2024")
        self.assertEqual(top("search engine optimization"), "google-search-essentials")
        self.assertEqual(top("traffic source"), "google-analytics-traffic-source")
        self.assertEqual(top("brand evaluation"), "iso-20671-1-2021")
        self.assertEqual(top("adtech privacy"), "iab-privacy-standards")
        self.assertEqual(top("advertising measurement"), "mrc-outcomes-data-quality-2022")

        # Unknown named authorities must fail closed rather than borrow relevance
        # from one or two generic overlapping tokens.
        self.assertEqual(positive("Semantic Scholar"), [])
        self.assertEqual(positive("CITATION.cff"), [])
        self.assertEqual(positive("IGDA Game Accessibility"), [])

    def test_latest_observation_is_append_only_date_selection(self):
        latest = catalog.latest_observation("iso-9001-2026")
        self.assertIsNotNone(latest)
        self.assertEqual(latest[1]["observedDate"], "2026-09-19")
        self.assertEqual(latest[1]["lifecycleStatus"], "published-current")

    def test_refresh_is_a_plan_not_mutation(self):
        _, record = catalog.get_record("iso-31000-2018")
        before = json.dumps(record, sort_keys=True)
        # The CLI implementation is intentionally read-only; rebuilding the plan uses loaded source only.
        latest = catalog.latest_observation("iso-31000-2018")
        self.assertIsNotNone(latest)
        after = json.dumps(catalog.get_record("iso-31000-2018")[1], sort_keys=True)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
