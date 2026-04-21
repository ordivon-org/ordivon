from pathlib import Path

from knowledge.wiki.service import MarkdownWikiService


def test_markdown_wiki_service_lists_documents(tmp_path: Path):
    reviews_dir = tmp_path / "reviews"
    reviews_dir.mkdir()

    older = reviews_dir / "review_BTC_USDT_20260417_0909.md"
    newer = reviews_dir / "review_ETH_USDT_20260417_0942.md"
    older.write_text("# older", encoding="utf-8")
    newer.write_text("# newer", encoding="utf-8")

    service = MarkdownWikiService(base_dir=tmp_path)
    documents = service.list_documents(section="reviews", limit=2)

    assert len(documents) == 2
    assert documents[0].document_id == newer.stem
    assert documents[1].document_id == older.stem
