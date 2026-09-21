from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "productions" / "ordivon-system-constellation-atlas" / "generate.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("system_constellation_atlas_generate", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main", str(path)], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "test"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "test@example.invalid"], check=True)
    (path / "README.md").write_text(f"# {path.name}\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "README.md"], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "-q", "-m", "init"], check=True)


class SystemConstellationAtlasTests(unittest.TestCase):
    def test_package_manifest_matches_current_package_bytes(self) -> None:
        production_root = GENERATOR.parent
        manifest = production_root / "manifest.sha256"
        rows = [line.split("  ", 1) for line in manifest.read_text(encoding="utf-8").splitlines()]
        self.assertTrue(rows)
        for expected, relative in rows:
            payload = (production_root / relative).read_bytes()
            actual = hashlib.sha256(payload).hexdigest()
            self.assertEqual(actual, expected, relative)

    def test_future_discovery_uses_canonical_monorepo_and_excludes_retired_lab(self) -> None:
        module = load_generator()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project_root = root / "projects"
            project_root.mkdir()
            init_repo(project_root / "ordivon-alpha")
            init_repo(project_root / "ordivon")
            init_repo(root / "workstation-lab")

            module.PROJECT_ROOT = project_root
            module.CANONICAL_MONOREPO = project_root / "ordivon"
            rows = module.discover()

        names = {row["name"] for row in rows}
        paths = {row["path"] for row in rows}
        self.assertEqual(names, {"ordivon", "ordivon-alpha"})
        self.assertNotIn(str(root / "workstation-lab"), paths)
        canonical = next(row for row in rows if row["name"] == "ordivon")
        self.assertEqual(canonical["group"], "monorepo")


if __name__ == "__main__":
    unittest.main()
