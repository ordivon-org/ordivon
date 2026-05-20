"""OpenFGA client for Ordivon governance authorization.

Replaces hardcoded Python authorization logic (authority_state.py transitions,
route_reviewers.py surface mapping, admit_artifact.py authority gates) with
OpenFGA relationship-based access control.

Architecture:
    OpenFGA stores: (user, relation, object) tuples
    Ordivon asks:   "Can user X perform action Y on object Z?"
    OpenFGA answers: ALLOW or DENY

Usage:
    from ordivon_governance_core.openfga_client import (
        OpenFGAClient, check_permission, can_approve_transition,
    )

    client = OpenFGAClient()
    allowed = await client.check(
        user="ordivon-core-maintainer",
        relation="can_approve_transition",
        object="governable_object:phase-7p-summit",
    )

Ordivon-specific convenience functions build on the base check():
    can_approve_transition(user, object_id) → bool
    can_review_domain(user, domain) → bool
    can_register_object(user, object_type) → bool
    can_close_debt(user, debt_id) → bool
"""

from __future__ import annotations

import os
import asyncio
from dataclasses import dataclass, field
from typing import Optional

# httpx is imported lazily — only when making requests

# ── OpenFGA API client ─────────────────────────────────────────────────────


@dataclass
class OpenFGAClient:
    """Lightweight OpenFGA client using REST API (no SDK dependency).

    Uses httpx for async HTTP. Falls back gracefully when OpenFGA is not
    available (returns DENY on all checks), so governance tools can call
    check() without worrying about OpenFGA uptime.

    Environment:
        OPENFGA_API_URL: OpenFGA API base URL (default: http://localhost:8081)
        OPENFGA_STORE_ID: Store ID (default: ordivon)
        OPENFGA_AUTH_TOKEN: Optional bearer token
    """

    base_url: str = field(default_factory=lambda: os.environ.get("OPENFGA_API_URL", "http://localhost:8081"))
    store_id: str = field(default_factory=lambda: os.environ.get("OPENFGA_STORE_ID", "ordivon"))
    auth_token: Optional[str] = field(default_factory=lambda: os.environ.get("OPENFGA_AUTH_TOKEN"))

    _available: Optional[bool] = None
    _resolved_store_id: Optional[str] = None

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.auth_token:
            h["Authorization"] = f"Bearer {self.auth_token}"
        return h

    async def _raw_request(self, method: str, path: str, json_data: dict | None = None) -> dict:
        """Make an OpenFGA API request. Returns parsed JSON or error dict."""
        import httpx  # lazy import — only when making requests

        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                if method == "POST":
                    resp = await client.post(url, headers=self._headers(), json=json_data)
                elif method == "GET":
                    resp = await client.get(url, headers=self._headers())
                else:
                    return {"error": f"Unsupported method: {method}"}
                resp.raise_for_status()
                return resp.json() if resp.content else {}
        except httpx.HTTPError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    async def ensure_store(self) -> bool:
        """Resolve or create the configured OpenFGA store.

        OPENFGA_STORE_ID may be either a real OpenFGA store id or a friendly
        store name such as "ordivon". OpenFGA assigns ids server-side, so local
        dev environments need this resolution step before tuple writes/checks.
        """
        if self._resolved_store_id:
            return True

        stores = {}
        for attempt in range(3):
            stores = await self._raw_request("GET", "stores")
            if "error" not in stores:
                break
            if attempt < 2:
                await asyncio.sleep(0.5)
        if "error" in stores:
            self._available = False
            return False

        for store in stores.get("stores", []):
            if store.get("id") == self.store_id or store.get("name") == self.store_id:
                self._resolved_store_id = store["id"]
                self._available = True
                return True

        created = {}
        for attempt in range(3):
            created = await self._raw_request("POST", "stores", {"name": self.store_id})
            if "error" not in created:
                break
            if attempt < 2:
                await asyncio.sleep(0.5)
        if "error" in created or not created.get("id"):
            self._available = False
            return False

        self._resolved_store_id = created["id"]
        self._available = True
        return True

    async def _request(self, method: str, path: str, json_data: dict | None = None) -> dict:
        """Make a store-scoped OpenFGA API request."""
        if not await self.ensure_store():
            return {"error": "OpenFGA store unavailable"}
        return await self._raw_request(method, f"stores/{self._resolved_store_id}/{path.lstrip('/')}", json_data)

    async def write_authorization_model(self, model: dict) -> str | None:
        """Write an authorization model and return its id."""
        result = await self._request("POST", "authorization-models", model)
        if "error" in result:
            return None
        return result.get("authorization_model_id")

    async def check(
        self,
        user: str,
        relation: str,
        object: str,
        contextual_tuples: list[dict] | None = None,
    ) -> bool:
        """Check if a user has a relation to an object.

        Args:
            user: User identifier (e.g. "user:ordivon-core-maintainer")
            relation: Relation to check (e.g. "can_approve_transition")
            object: Object identifier (e.g. "governable_object:phase-7p-summit")
            contextual_tuples: Optional list of tuples for context-aware checks

        Returns:
            True if allowed, False if denied or OpenFGA unavailable.
        """
        body = {
            "tuple_key": {
                "user": user,
                "relation": relation,
                "object": object,
            },
        }
        if contextual_tuples:
            body["contextual_tuples"] = {
                "tuple_keys": [
                    {"user": t["user"], "relation": t["relation"], "object": t["object"]} for t in contextual_tuples
                ]
            }

        result = await self._request("POST", "check", body)
        if "error" in result:
            self._available = False
            return False

        self._available = True
        return result.get("allowed", False)

    async def write_tuple(self, user: str, relation: str, object: str) -> bool:
        """Write a relationship tuple to OpenFGA.

        Returns True on success, False on failure.
        """
        body = {"writes": {"tuple_keys": [{"user": user, "relation": relation, "object": object}]}}
        result = await self._request("POST", "write", body)
        if "error" not in result:
            return True
        # OpenFGA rejects duplicate tuple writes. Treat an already-present tuple
        # as success so bootstrap and smoke checks stay idempotent.
        return await self.check(user, relation, object)

    async def delete_tuple(self, user: str, relation: str, object: str) -> bool:
        """Delete a relationship tuple from OpenFGA.

        Returns True on success, False on failure.
        """
        body = {"deletes": {"tuple_keys": [{"user": user, "relation": relation, "object": object}]}}
        result = await self._request("POST", "write", body)
        return "error" not in result

    async def list_objects(self, user: str, relation: str, object_type: str) -> list[str]:
        """List objects of a type that a user has a relation to.

        Returns list of object IDs.
        """
        body = {
            "user": user,
            "relation": relation,
            "type": object_type,
        }
        result = await self._request("POST", "list-objects", body)
        if "error" in result:
            return []
        return result.get("objects", [])

    async def list_users(self, object: str, relation: str) -> list[dict]:
        """List users who have a relation to an object.

        Returns list of user dicts.
        """
        body = {
            "object": object,
            "relation": relation,
            "user_filters": [],
        }
        result = await self._request("POST", "list-users", body)
        if "error" in result:
            return []
        return result.get("users", [])

    def available(self) -> bool:
        """Check if OpenFGA is available. Returns cached result after first check."""
        return self._available is True


# ── Global client instance ─────────────────────────────────────────────────

_client: Optional[OpenFGAClient] = None


def get_client() -> OpenFGAClient:
    global _client
    if _client is None:
        _client = OpenFGAClient()
    return _client


# ── Ordivon Convenience Functions ──────────────────────────────────────────
#
# These map Ordivon governance concepts to OpenFGA check() calls.
# User-facing: call these directly, no need to construct OpenFGA tuples manually.


async def can_approve_transition(user: str, object_id: str) -> bool:
    """Can a user approve a transition on a governable object?

    Checks: user is approver of the object's domain, OR org admin.

    Usage:
        allowed = await can_approve_transition(
            "user:ordivon-core-maintainer",
            "phase-7p-summit",
        )
    """
    client = get_client()
    return await client.check(
        user=f"user:{user}",
        relation="can_approve_transition",
        object=f"governable_object:{object_id}",
    )


async def can_review_domain(user: str, domain_name: str) -> bool:
    """Can a user review objects in a domain?

    Checks: user is reviewer of the domain.

    Usage:
        allowed = await can_review_domain(
            "ordivon-core-maintainer",
            "documentation",
        )
    """
    client = get_client()
    return await client.check(
        user=f"user:{user}",
        relation="reviewer",
        object=f"domain:{domain_name}",
    )


async def can_register_object(user: str, object_type: str, domain_name: str) -> bool:
    """Can a user register a new object of a given type in a domain?

    Checks: user is maintainer of the domain.

    Usage:
        allowed = await can_register_object(
            "ordivon-core-maintainer",
            "document",
            "documentation",
        )
    """
    client = get_client()
    return await client.check(
        user=f"user:{user}",
        relation="maintainer",
        object=f"domain:{domain_name}",
    )


async def can_close_debt(user: str, debt_id: str) -> bool:
    """Can a user close a debt?

    Checks: user is owner of the debt OR approver of the debt's domain.

    Usage:
        allowed = await can_close_debt(
            "ordivon-core-maintainer",
            "VD-2026-04-30-001",
        )
    """
    client = get_client()
    return await client.check(
        user=f"user:{user}",
        relation="can_close",
        object=f"debt:{debt_id}",
    )


async def can_activate_policy(user: str, policy_id: str) -> bool:
    """Can a user activate a candidate rule as policy?

    Checks: user is approver of the policy's domain OR org admin.

    Usage:
        allowed = await can_activate_policy(
            "ordivon-core-maintainer",
            "candidate-rule-dogfood",
        )
    """
    client = get_client()
    return await client.check(
        user=f"user:{user}",
        relation="can_activate",
        object=f"policy:{policy_id}",
    )


async def can_verify_receipt(user: str, receipt_id: str) -> bool:
    """Can a user verify a receipt?

    Checks: user is reviewer of the receipt's parent object's domain.

    Usage:
        allowed = await can_verify_receipt(
            "ordivon-core-maintainer",
            "aos-structural-gap-1-closure-receipt",
        )
    """
    client = get_client()
    return await client.check(
        user=f"user:{user}",
        relation="can_verify",
        object=f"receipt:{receipt_id}",
    )


# ── Bootstrap: seed initial authorization tuples ───────────────────────────


DEFAULT_AUTHORIZATION_TUPLES = [
    # Ordivon organization
    ("user:ordivon-core-maintainer", "admin", "organization:ordivon"),
    # Teams
    ("user:ordivon-core-maintainer", "member", "team:ordivon-core"),
    ("user:ordivon-core-maintainer", "member", "team:governance"),
    # Documentation domain
    ("team:governance#member", "maintainer", "domain:documentation"),
    ("team:governance#member", "reviewer", "domain:documentation"),
    ("user:ordivon-core-maintainer", "approver", "domain:documentation"),
    ("team:ordivon-core#member", "viewer", "domain:documentation"),
    # Implementation domain
    ("team:ordivon-core#member", "maintainer", "domain:implementation"),
    ("team:ordivon-core#member", "reviewer", "domain:implementation"),
    ("user:ordivon-core-maintainer", "approver", "domain:implementation"),
    ("team:ordivon-core#member", "viewer", "domain:implementation"),
    # Policy domain
    ("team:governance#member", "maintainer", "domain:policy"),
    ("team:governance#member", "reviewer", "domain:policy"),
    ("user:ordivon-core-maintainer", "approver", "domain:policy"),
    ("team:ordivon-core#member", "viewer", "domain:policy"),
    # Tooling domain
    ("team:ordivon-core#member", "maintainer", "domain:tooling"),
    ("team:ordivon-core#member", "reviewer", "domain:tooling"),
    ("user:ordivon-core-maintainer", "approver", "domain:tooling"),
    # Runtime domain
    ("team:ordivon-core#member", "maintainer", "domain:runtime"),
    ("user:ordivon-core-maintainer", "approver", "domain:runtime"),
    # Phases
    ("team:governance", "owner", "phase:dg-1"),
    ("team:governance", "owner", "phase:dg-2"),
    ("team:ordivon-core", "owner", "phase:mr-0"),
]


async def bootstrap_authorization(dry_run: bool = False) -> dict:
    """Seed OpenFGA with default Ordivon authorization tuples.

    Returns dict with counts of written/skipped/errors.
    """
    client = get_client()
    results = {"written": 0, "skipped": 0, "errors": 0}

    for user, relation, obj in DEFAULT_AUTHORIZATION_TUPLES:
        if dry_run:
            results["written"] += 1
            continue
        ok = await client.write_tuple(user, relation, obj)
        if ok:
            results["written"] += 1
        else:
            results["errors"] += 1

    return results
