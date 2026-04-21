from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(slots=True)
class MarkdownKnowledgeDocument:
    document_id: str
    title: str
    path: str
    created_at: str


class MarkdownWikiService:
    """Knowledge-layer access to markdown wiki content during migration."""

    def __init__(self, base_dir: str | Path = "wiki") -> None:
        self.base_dir = Path(base_dir)

    def list_documents(self, section: str, limit: int = 10) -> list[MarkdownKnowledgeDocument]:
        section_dir = self.base_dir / section
        if not section_dir.exists():
            return []

        files = sorted(
            section_dir.glob("*.md"),
            key=lambda path: (path.stat().st_mtime, path.name),
            reverse=True,
        )[:limit]

        return [self._to_document(path) for path in files]

    def _to_document(self, path: Path) -> MarkdownKnowledgeDocument:
        return MarkdownKnowledgeDocument(
            document_id=path.stem,
            title=path.stem.replace("_", " "),
            path=path.as_posix(),
            created_at=datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        )

    def write_document(self, section: str, document_id: str, content: str) -> str:
        """Write content to a markdown document in the wiki."""
        section_dir = self.base_dir / section
        section_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = section_dir / f"{document_id}.md"
        file_path.write_text(content, encoding="utf-8")
        
        return file_path.as_posix()
