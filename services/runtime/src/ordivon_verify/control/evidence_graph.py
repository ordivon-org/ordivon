"""Evidence Graph — connects claims to evidence to artifacts to verification.

The Evidence Graph is Ordivon's trust fabric. For every claim in a receipt
(e.g. "all_required_docs_registered"), it traces back to:
  - What evidence supports it (registry_diff, checker_output)
  - What verification produced that evidence (document-registry gate)
  - What artifacts were involved (document-registry.jsonl)

This enables:
  - Machine verification: "does this receipt actually have evidence?"
  - Tamper detection: "does the evidence hash match?"
  - Audit trail: "show me everything that supports this claim"
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EvidenceNode:
    """A piece of evidence in the graph."""

    node_id: str
    node_type: str  # claim | evidence | verification | artifact
    label: str
    metadata: dict = field(default_factory=dict)


@dataclass
class EvidenceEdge:
    """A relationship between two nodes."""

    source: str  # node_id of the source
    target: str  # node_id of the target
    relation: str  # supported_by | produced_by | verified_by | references


@dataclass
class EvidenceGraph:
    """Directed graph connecting governance claims to their evidence."""

    nodes: list[EvidenceNode] = field(default_factory=list)
    edges: list[EvidenceEdge] = field(default_factory=list)

    def add_claim(self, claim_id: str, description: str, **meta) -> EvidenceNode:
        node = EvidenceNode(claim_id, "claim", description, meta)
        self.nodes.append(node)
        return node

    def add_evidence(self, evidence_id: str, evidence_type: str, path: str, **meta) -> EvidenceNode:
        node = EvidenceNode(
            evidence_id, "evidence", f"{evidence_type}: {path}", {"type": evidence_type, "path": path, **meta}
        )
        self.nodes.append(node)
        return node

    def add_verification(self, gate_id: str, passed: bool, **meta) -> EvidenceNode:
        node = EvidenceNode(
            gate_id, "verification", f"{'✅' if passed else '❌'} {gate_id}", {"passed": passed, **meta}
        )
        self.nodes.append(node)
        return node

    def add_artifact(self, path: str, **meta) -> EvidenceNode:
        node = EvidenceNode(path, "artifact", path, meta)
        self.nodes.append(node)
        return node

    def link(self, source: str, target: str, relation: str) -> EvidenceEdge:
        edge = EvidenceEdge(source, target, relation)
        self.edges.append(edge)
        return edge

    # ── Builders ──────────────────────────────────────────────────

    @classmethod
    def from_receipt(cls, receipt: dict) -> EvidenceGraph:
        """Build an evidence graph from a closure receipt."""
        g = cls()
        stage_id = receipt.get("stage_id", "unknown")

        # Claims from closure predicates
        for pred in receipt.get("closure_predicates", []):
            claim_id = f"claim:{stage_id}:{pred['id']}"
            g.add_claim(claim_id, pred["id"], satisfied=pred.get("satisfied", False))

            if pred.get("evidence_ref"):
                g.add_evidence(f"ev:{stage_id}:{pred['id']}", "receipt_reference", pred["evidence_ref"])
                g.link(claim_id, f"ev:{stage_id}:{pred['id']}", "supported_by")

        # Evidence from evidence_produced
        for ev in receipt.get("evidence_produced", []):
            ev_id = f"ev:{stage_id}:{ev['type']}"
            g.add_evidence(ev_id, ev.get("type", "unknown"), ev.get("path", ""), hash=ev.get("hash", ""))

        # Verification results
        for v in receipt.get("verification_results", []):
            v_id = f"verify:{stage_id}:{v['id']}"
            g.add_verification(
                v_id, v.get("passed", False), exit_code=v.get("exit_code"), hash=v.get("output_hash", "")
            )
            # Link verification to its evidence
            if v.get("output_hash"):
                ev_id = f"ev:{stage_id}:{v['id']}"
                g.link(v_id, ev_id, "produced_by")

        # Artifacts from files_changed
        for f in receipt.get("files_changed", []):
            art_id = f"artifact:{f}"
            g.add_artifact(f)
            # Link artifacts to the stage
            g.link(f"claim:{stage_id}:all_required_docs_registered", art_id, "references")

        return g

    # ── Queries ───────────────────────────────────────────────────

    def find_unsupported_claims(self) -> list[str]:
        """Find claims that have no supporting evidence."""
        supported = {e.target for e in self.edges if e.relation == "supported_by"}
        claims = {n.node_id for n in self.nodes if n.node_type == "claim"}
        return list(claims - supported)

    def find_unverified_claims(self) -> list[str]:
        """Find claims not linked to any verification."""
        verified = set()
        for e in self.edges:
            if e.relation == "produced_by":
                verified.add(e.source)
        claims = {n.node_id for n in self.nodes if n.node_type == "claim"}
        return list(claims - verified)

    def summary(self) -> dict:
        """Return a summary of the graph."""
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "claims": sum(1 for n in self.nodes if n.node_type == "claim"),
            "evidence": sum(1 for n in self.nodes if n.node_type == "evidence"),
            "verifications": sum(1 for n in self.nodes if n.node_type == "verification"),
            "artifacts": sum(1 for n in self.nodes if n.node_type == "artifact"),
            "unsupported_claims": len(self.find_unsupported_claims()),
            "unverified_claims": len(self.find_unverified_claims()),
        }
