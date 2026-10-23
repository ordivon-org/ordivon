# GENERATED FILE — DO NOT EDIT BY HAND.
# Source: profiles/research/capability-index/research-capability-index-r1.json
# Provider bindings: .agents/skills/research-capability-routing/references/research-capability-routing-r1.json
# indexDigest=sha256:7dc68e6907560cafd4efb98fd75c0d5471390696b82d4ed42c93ecf7e439e9a0 routingProfileDigest=sha256:a375d6e7de1d8ba9b6cffbfa709f68aa4f70fca2b449ba6cfae9387d78f792ea
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InvocationRecipeSpec:
    recipe_id: str
    kind: str
    owner_id: str
    command: tuple[str, ...] = ()
    note: str = ""


@dataclass(frozen=True)
class ResearchCapabilitySpec:
    capability: str
    description: str
    tags: tuple[str, ...]
    semantic_owner: str
    completion_owner: str
    study_types: tuple[str, ...]
    preferred_skills: tuple[str, ...]
    invocation_recipes: tuple[InvocationRecipeSpec, ...]
    source_refs: tuple[str, ...]
    execution_capability: str | None = None
    truth_boundary: str = ""


_PROJECTED = [
    {
        "capability": "research.literature.discovery",
        "completion_owner": "study",
        "description": "Discover scholarly records and source metadata through mature scholarly "
        "providers without promoting search results into scientific truth.",
        "execution_capability": None,
        "invocation_recipes": [
            {
                "command": [],
                "kind": "skill",
                "note": "Resolve an exact current Skill binding first; discovery does "
                "not grant source quality, eligibility, or synthesis authority.",
                "owner_id": "skills",
                "recipe_id": "skill-explicit",
            }
        ],
        "preferred_skills": ["paper-lookup"],
        "semantic_owner": "study.method-and-source-authorities",
        "source_refs": [
            "catalogs/capabilities/packages/research.md",
            "docs/architecture/RESEARCH_STUDY_AUTHORITY_R1.md",
            "profiles/research/scholarly-intelligence/SCHOLARLY_INTELLIGENCE_R2.md",
        ],
        "study_types": ["systematic-review", "replication-or-reproduction", "meta-science"],
        "tags": ["research", "literature", "scholarly", "openalex", "crossref", "papers"],
        "truth_boundary": "This Research route is non-authoritative composition metadata. Study/domain "
        "owners retain scientific truth and completion authority; Skills remain "
        "advisory; Runtime owns only physical execution evidence.",
    },
    {
        "capability": "research.citation.metadata",
        "completion_owner": "study",
        "description": "Verify scholarly citation and DOI metadata while preserving provider/source "
        "authority.",
        "execution_capability": None,
        "invocation_recipes": [
            {
                "command": [],
                "kind": "skill",
                "note": "Resolve exact citation Skill bytes before activation.",
                "owner_id": "skills",
                "recipe_id": "skill-explicit",
            }
        ],
        "preferred_skills": ["citation-management"],
        "semantic_owner": "study.bibliographic-policy-and-source-authorities",
        "source_refs": [
            "catalogs/capabilities/packages/research.md",
            "docs/architecture/RESEARCH_STUDY_AUTHORITY_R1.md",
            "profiles/research/scholarly-intelligence/SCHOLARLY_INTELLIGENCE_R2.md",
            "profiles/research/publication/publication-closure-profile-r2.json",
        ],
        "study_types": ["all"],
        "tags": ["research", "citation", "doi", "crossref", "bibtex", "csl"],
        "truth_boundary": "This Research route is non-authoritative composition metadata. Study/domain "
        "owners retain scientific truth and completion authority; Skills remain "
        "advisory; Runtime owns only physical execution evidence.",
    },
    {
        "capability": "research.experimental.design",
        "completion_owner": "study",
        "description": "Compose hypothesis and experimental-design procedures under the applicable "
        "method authority.",
        "execution_capability": None,
        "invocation_recipes": [
            {
                "command": [],
                "kind": "skill",
                "note": "Procedural advice remains subordinate to the Study's method authority.",
                "owner_id": "skills",
                "recipe_id": "skill-explicit",
            }
        ],
        "preferred_skills": ["experimental-design", "hypothesis-generation"],
        "semantic_owner": "study.method-authority",
        "source_refs": [
            "catalogs/capabilities/packages/research.md",
            "docs/architecture/RESEARCH_STUDY_AUTHORITY_R1.md",
            "profiles/research/scholarly-intelligence/SCHOLARLY_INTELLIGENCE_R2.md",
        ],
        "study_types": [
            "empirical-software-engineering",
            "data-science-machine-learning",
            "benchmarking-software-systems",
        ],
        "tags": ["research", "hypothesis", "experimental-design", "method", "protocol"],
        "truth_boundary": "This Research route is non-authoritative composition metadata. Study/domain "
        "owners retain scientific truth and completion authority; Skills remain "
        "advisory; Runtime owns only physical execution evidence.",
    },
    {
        "capability": "research.statistical.analysis",
        "completion_owner": "study",
        "description": "Select and apply statistical analysis under Study-owned estimand, dependence, "
        "uncertainty, and reporting semantics.",
        "execution_capability": None,
        "invocation_recipes": [
            {
                "command": [],
                "kind": "skill",
                "note": "Skill selection cannot infer the estimand, dependence model, or "
                "claim ceiling.",
                "owner_id": "skills",
                "recipe_id": "skill-explicit",
            }
        ],
        "preferred_skills": ["statistical-analysis"],
        "semantic_owner": "study.statistical-method-authority",
        "source_refs": [
            "catalogs/capabilities/packages/research.md",
            "docs/architecture/RESEARCH_STUDY_AUTHORITY_R1.md",
            "profiles/research/scholarly-intelligence/SCHOLARLY_INTELLIGENCE_R2.md",
        ],
        "study_types": ["all"],
        "tags": ["research", "statistics", "inference", "effect-size", "power", "bayesian"],
        "truth_boundary": "This Research route is non-authoritative composition metadata. Study/domain "
        "owners retain scientific truth and completion authority; Skills remain "
        "advisory; Runtime owns only physical execution evidence.",
    },
    {
        "capability": "research.data.exploration",
        "completion_owner": "study",
        "description": "Perform bounded exploratory analysis using Study-owned data and explicit data "
        "contracts.",
        "execution_capability": None,
        "invocation_recipes": [
            {
                "command": [],
                "kind": "skill",
                "note": "EDA outputs are observations, not confirmatory evidence by default.",
                "owner_id": "skills",
                "recipe_id": "skill-explicit",
            }
        ],
        "preferred_skills": ["exploratory-data-analysis"],
        "semantic_owner": "study.data-and-method-authority",
        "source_refs": [
            "catalogs/capabilities/packages/research.md",
            "docs/architecture/RESEARCH_STUDY_AUTHORITY_R1.md",
            "profiles/research/scholarly-intelligence/SCHOLARLY_INTELLIGENCE_R2.md",
        ],
        "study_types": ["all"],
        "tags": ["research", "eda", "data", "duckdb", "pandas", "polars", "pandera"],
        "truth_boundary": "This Research route is non-authoritative composition metadata. Study/domain "
        "owners retain scientific truth and completion authority; Skills remain "
        "advisory; Runtime owns only physical execution evidence.",
    },
    {
        "capability": "research.visualization",
        "completion_owner": "study",
        "description": "Create or audit truthful publication-ready scientific figures.",
        "execution_capability": None,
        "invocation_recipes": [
            {
                "command": [],
                "kind": "skill",
                "note": "Figure production does not upgrade claim support or publication standing.",
                "owner_id": "skills",
                "recipe_id": "skill-explicit",
            }
        ],
        "preferred_skills": ["scientific-visualization"],
        "semantic_owner": "study.figure-and-claim-authority",
        "source_refs": [
            "catalogs/capabilities/packages/research.md",
            "docs/architecture/RESEARCH_STUDY_AUTHORITY_R1.md",
            "profiles/research/scholarly-intelligence/SCHOLARLY_INTELLIGENCE_R2.md",
            "profiles/research/publication/perceptual-conformance-profile-r1.json",
        ],
        "study_types": ["all"],
        "tags": ["research", "figure", "visualization", "publication", "matplotlib"],
        "truth_boundary": "This Research route is non-authoritative composition metadata. Study/domain "
        "owners retain scientific truth and completion authority; Skills remain "
        "advisory; Runtime owns only physical execution evidence.",
    },
    {
        "capability": "research.peer.review",
        "completion_owner": "study",
        "description": "Perform evidence-bounded manuscript review without taking Study decision "
        "authority.",
        "execution_capability": None,
        "invocation_recipes": [
            {
                "command": [],
                "kind": "skill",
                "note": "Reviewer judgment remains evidence/advice, not automatic "
                "scientific or submission authority.",
                "owner_id": "skills",
                "recipe_id": "skill-explicit",
            }
        ],
        "preferred_skills": ["peer-review", "scientific-critical-thinking"],
        "semantic_owner": "study-and-review-protocol",
        "source_refs": [
            "catalogs/capabilities/packages/research.md",
            "docs/architecture/RESEARCH_STUDY_AUTHORITY_R1.md",
            "profiles/research/scholarly-intelligence/SCHOLARLY_INTELLIGENCE_R2.md",
        ],
        "study_types": ["all"],
        "tags": ["research", "peer-review", "critique", "evidence", "reproducibility"],
        "truth_boundary": "This Research route is non-authoritative composition metadata. Study/domain "
        "owners retain scientific truth and completion authority; Skills remain "
        "advisory; Runtime owns only physical execution evidence.",
    },
    {
        "capability": "research.scientific.writing",
        "completion_owner": "study",
        "description": "Draft or audit scientific text with explicit evidence provenance and claim "
        "boundaries.",
        "execution_capability": None,
        "invocation_recipes": [
            {
                "command": [],
                "kind": "skill",
                "note": "Writing may express accepted evidence but cannot create new "
                "scientific support by prose.",
                "owner_id": "skills",
                "recipe_id": "skill-explicit",
            }
        ],
        "preferred_skills": ["scientific-writing"],
        "semantic_owner": "study.claim-and-manuscript-authority",
        "source_refs": [
            "catalogs/capabilities/packages/research.md",
            "docs/architecture/RESEARCH_STUDY_AUTHORITY_R1.md",
            "profiles/research/scholarly-intelligence/SCHOLARLY_INTELLIGENCE_R2.md",
        ],
        "study_types": ["all"],
        "tags": ["research", "writing", "manuscript", "report", "evidence"],
        "truth_boundary": "This Research route is non-authoritative composition metadata. Study/domain "
        "owners retain scientific truth and completion authority; Skills remain "
        "advisory; Runtime owns only physical execution evidence.",
    },
    {
        "capability": "research.study.birth",
        "completion_owner": "study",
        "description": "Create or validate a Research Study birth contract with exact method-authority "
        "and data-plane bindings.",
        "execution_capability": None,
        "invocation_recipes": [
            {
                "command": ["ordivon-research-study"],
                "kind": "owner-cli",
                "note": "The CLI is owned by Research-v2. Its frozen birth-policy digest "
                "and Study output, not Gateway, are the authority.",
                "owner_id": "research-v2",
                "recipe_id": "research-v2-cli",
            }
        ],
        "preferred_skills": [],
        "semantic_owner": "research-v2.study-birth-contract",
        "source_refs": [
            "docs/architecture/RESEARCH_STUDY_AUTHORITY_R1.md",
            "research-v2:profiles/research_birth_policy.toml",
            "research-v2:src/ordivon_research/study_birth.py",
        ],
        "study_types": ["all"],
        "tags": ["research", "study", "birth", "authority", "profile", "admission"],
        "truth_boundary": "This Research route is non-authoritative composition metadata. Study/domain "
        "owners retain scientific truth and completion authority; Skills remain "
        "advisory; Runtime owns only physical execution evidence.",
    },
    {
        "capability": "research.study.verify",
        "completion_owner": "study",
        "description": "Run the repository-owned portable Research profile/currentness verification "
        "recipe.",
        "execution_capability": "execution.linux",
        "invocation_recipes": [
            {
                "command": ["mise", "run", "research-study:verify"],
                "kind": "mise-task",
                "note": "Canonical recipe binds its own transient jsonschema dependency "
                "through uv; do not replace it with ad-hoc system Python "
                "invocation.",
                "owner_id": "ordivon-monorepo",
                "recipe_id": "monorepo-mise-research-study-verify",
            }
        ],
        "preferred_skills": [],
        "semantic_owner": "research-profile-verifiers",
        "source_refs": [
            "mise.toml",
            "profiles/research/scholarly-intelligence/SCHOLARLY_INTELLIGENCE_R2.md",
        ],
        "study_types": ["all"],
        "tags": ["research", "verify", "currentness", "profile", "mise", "uv"],
        "truth_boundary": "This Research route is non-authoritative composition metadata. Study/domain "
        "owners retain scientific truth and completion authority; Skills remain "
        "advisory; Runtime owns only physical execution evidence.",
    },
    {
        "capability": "research.publication.closure",
        "completion_owner": "study-and-human-submission-authority",
        "description": "Apply the shared publication-closure profile while keeping science, rendering, "
        "release, and human submission authority separate.",
        "execution_capability": None,
        "invocation_recipes": [
            {
                "command": [],
                "kind": "skill",
                "note": "Project-local Skill may be used only after exact context-aware "
                "resolution.",
                "owner_id": "skills",
                "recipe_id": "skill-explicit",
            }
        ],
        "preferred_skills": ["research-publication-closure"],
        "semantic_owner": "study.publication-authority",
        "source_refs": [
            "profiles/research/publication/publication-closure-profile-r2.json",
            ".agents/skills/research-publication-closure/SKILL.md",
        ],
        "study_types": ["all"],
        "tags": ["research", "publication", "closure", "submission", "artifact"],
        "truth_boundary": "This Research route is non-authoritative composition metadata. Study/domain "
        "owners retain scientific truth and completion authority; Skills remain "
        "advisory; Runtime owns only physical execution evidence.",
    },
    {
        "capability": "research.publication.perceptual-conformance",
        "completion_owner": "study.publication-authority",
        "description": "Run independent rendered-artifact perceptual conformance without substituting "
        "machine QA for human or scientific authority.",
        "execution_capability": None,
        "invocation_recipes": [
            {
                "command": [],
                "kind": "skill",
                "note": "Observer independence and exact carrier binding remain profile "
                "requirements.",
                "owner_id": "skills",
                "recipe_id": "skill-explicit",
            }
        ],
        "preferred_skills": ["research-publication-perceptual-conformance"],
        "semantic_owner": "publication-perceptual-observer-protocol",
        "source_refs": [
            "profiles/research/publication/perceptual-conformance-profile-r1.json",
            ".agents/skills/research-publication-perceptual-conformance/SKILL.md",
        ],
        "study_types": ["all"],
        "tags": ["research", "publication", "perceptual", "layout", "figure", "review"],
        "truth_boundary": "This Research route is non-authoritative composition metadata. Study/domain "
        "owners retain scientific truth and completion authority; Skills remain "
        "advisory; Runtime owns only physical execution evidence.",
    },
    {
        "capability": "research.scholarly.intelligence",
        "completion_owner": "study",
        "description": "Project Study-owned scholarly state across independent axes without creating a "
        "universal scientific ontology.",
        "execution_capability": "execution.linux",
        "invocation_recipes": [
            {
                "command": ["mise", "run", "research-study:verify"],
                "kind": "mise-task",
                "note": "Axis-local closure never transfers authority to another scholarly axis.",
                "owner_id": "ordivon-monorepo",
                "recipe_id": "monorepo-mise-research-study-verify",
            }
        ],
        "preferred_skills": [],
        "semantic_owner": "study",
        "source_refs": [
            "profiles/research/scholarly-intelligence/SCHOLARLY_INTELLIGENCE_R2.md",
            "profiles/research/scholarly-intelligence/scholarly-intelligence-profile-v1.schema.json",
        ],
        "study_types": ["all"],
        "tags": [
            "research",
            "scholarly",
            "claims",
            "evidence",
            "review",
            "publication",
            "currentness",
        ],
        "truth_boundary": "This Research route is non-authoritative composition metadata. Study/domain "
        "owners retain scientific truth and completion authority; Skills remain "
        "advisory; Runtime owns only physical execution evidence.",
    },
]


def research_capabilities() -> dict[str, ResearchCapabilitySpec]:
    values: list[ResearchCapabilitySpec] = []
    for item in _PROJECTED:
        recipes = tuple(
            InvocationRecipeSpec(**{**recipe, "command": tuple(recipe["command"])})
            for recipe in item["invocation_recipes"]
        )
        values.append(
            ResearchCapabilitySpec(
                capability=item["capability"],
                description=item["description"],
                tags=tuple(item["tags"]),
                semantic_owner=item["semantic_owner"],
                completion_owner=item["completion_owner"],
                study_types=tuple(item["study_types"]),
                preferred_skills=tuple(item["preferred_skills"]),
                invocation_recipes=recipes,
                source_refs=tuple(item["source_refs"]),
                execution_capability=item["execution_capability"],
                truth_boundary=item["truth_boundary"],
            )
        )
    return {value.capability: value for value in values}
