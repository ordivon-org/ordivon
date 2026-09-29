from __future__ import annotations

import importlib.util
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from artifact_core.bindings import CapabilityBinding
from artifact_core.contracts import sha256_file

ROOT = Path(__file__).resolve().parents[1]
VerifierFunction = Callable[..., dict[str, Any]]


@dataclass(frozen=True)
class VerifierPlugin:
    """One admitted verifier implementation behind an explicit capability binding."""

    binding: CapabilityBinding
    function: VerifierFunction
    implementation_path: Path
    implementation_sha256: str

    def verify(
        self,
        subject: Path,
        evidence_directory: Path,
        *,
        object_contract: Path | None = None,
    ) -> dict[str, Any]:
        if self.binding.object_contract_required:
            if object_contract is None:
                raise ValueError(
                    f"Artifact profile requires an object contract: {self.binding.profile_id}"
                )
            result = self.function(subject, object_contract, evidence_directory)
        else:
            result = self.function(subject, evidence_directory)
        if not isinstance(result, dict):
            raise TypeError("Artifact verifier plugin must return a dict")
        return result

    def identity(self) -> dict[str, Any]:
        return {
            "capabilityId": self.binding.capability_id,
            "profileId": self.binding.profile_id,
            "operation": self.binding.operation,
            "entrypoint": {
                "module": self.binding.entrypoint.module,
                "callable": self.binding.entrypoint.callable,
            },
            "implementationSha256": self.implementation_sha256,
            "standing": self.binding.standing,
            "standingPath": str(self.binding.standing_path),
            "standingSha256": self.binding.standing_sha256,
            "objectContractRequired": self.binding.object_contract_required,
        }


def resolve_verifier_plugin(
    binding: CapabilityBinding,
    *,
    artifact_root: Path = ROOT,
) -> VerifierPlugin:
    if binding.operation != "verify":
        raise ValueError(f"VerifierPlugin requires a verify binding: {binding.operation}")
    path = (artifact_root / binding.entrypoint.module).resolve()
    if artifact_root.resolve() not in path.parents:
        raise ValueError("verifier implementation escaped Artifact root")
    if not path.is_file():
        raise RuntimeError(f"verifier implementation is absent: {path}")
    spec = importlib.util.spec_from_file_location(
        "artifact_verifier_plugin_" + path.stem,
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load verifier module: {binding.entrypoint.module}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fn = getattr(module, binding.entrypoint.callable, None)
    if not callable(fn):
        raise RuntimeError(
            "verifier function missing: "
            f"{binding.entrypoint.module}:{binding.entrypoint.callable}"
        )
    return VerifierPlugin(
        binding=binding,
        function=fn,
        implementation_path=path,
        implementation_sha256=sha256_file(path),
    )
