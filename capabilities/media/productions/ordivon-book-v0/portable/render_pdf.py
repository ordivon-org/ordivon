#!/usr/bin/env python3
"""Render the exact approved Book MDX into a derived Typst/PDF carrier.

`book.mdx` remains semantic authority. This converter is deliberately production-local,
fail-closed on unknown Markdown token types, and emits a receipt binding the source
Digest and structural census to the generated Typst projection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Iterable

from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode

EXPECTED_SOURCE_SHA256 = "14e5e15b9223cf6beee4ce3981eebc197c837f899948140e6daf96cfca6597c4"
ALLOWED_BLOCK = {
    "root", "heading", "paragraph", "fence", "blockquote", "bullet_list",
    "ordered_list", "list_item", "hr", "table", "thead", "tbody", "tr", "th", "td",
}
ALLOWED_INLINE = {"inline", "text", "strong", "code_inline", "link", "softbreak"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def q(value: str) -> str:
    # JSON string literals are compatible with the Typst string escapes used here.
    return json.dumps(value, ensure_ascii=False)


def children(node: SyntaxTreeNode) -> list[SyntaxTreeNode]:
    return list(node.children or [])


def render_inline(node: SyntaxTreeNode) -> str:
    t = node.type
    if t == "inline":
        return "".join(render_inline(c) for c in children(node))
    if t == "text":
        return f"#text({q(node.content or '')})"
    if t == "code_inline":
        return f"#raw({q(node.content or '')})"
    if t == "strong":
        return "#strong[" + "".join(render_inline(c) for c in children(node)) + "]"
    if t == "link":
        inner = "".join(render_inline(c) for c in children(node))
        href = (node.attrs or {}).get("href", "")
        # Relative repository links are not valid standalone-PDF destinations. Preserve
        # their visible text but do not manufacture a false portable link target.
        if href.startswith("http://") or href.startswith("https://") or href.startswith("mailto:"):
            return f"#link({q(href)})[" + inner + "]"
        return inner
    if t == "softbreak":
        return "#linebreak()"
    raise ValueError(f"unsupported inline token: {t}")


def render_flow(nodes: Iterable[SyntaxTreeNode]) -> str:
    return "".join(render_block(n) for n in nodes)


def list_items(node: SyntaxTreeNode) -> str:
    rendered = []
    for item in children(node):
        if item.type != "list_item":
            raise ValueError(f"unexpected {node.type} child: {item.type}")
        rendered.append("[" + render_flow(children(item)).strip() + "]")
    fn = "list" if node.type == "bullet_list" else "enum"
    args = ",\n  ".join(rendered)
    return f"#{fn}(\n  {args},\n)\n\n"


def table_cells(node: SyntaxTreeNode) -> tuple[int, list[str]]:
    rows: list[list[tuple[str, str]]] = []
    for section in children(node):
        if section.type not in {"thead", "tbody"}:
            raise ValueError(f"unexpected table section: {section.type}")
        for row in children(section):
            if row.type != "tr":
                raise ValueError(f"unexpected table row: {row.type}")
            cells: list[tuple[str, str]] = []
            for cell in children(row):
                if cell.type not in {"th", "td"}:
                    raise ValueError(f"unexpected table cell: {cell.type}")
                body = render_flow(children(cell)).strip()
                cells.append((cell.type, body))
            rows.append(cells)
    if not rows:
        return 0, []
    cols = max(len(r) for r in rows)
    if any(len(r) != cols for r in rows):
        raise ValueError("ragged Markdown table is not admitted for portable rendering")
    out: list[str] = []
    for row in rows:
        for kind, body in row:
            out.append(("strong[" + body + "]") if kind == "th" else ("[" + body + "]"))
    return cols, out


def render_block(node: SyntaxTreeNode) -> str:
    t = node.type
    if t == "root":
        return render_flow(children(node))
    if t == "inline":
        return render_inline(node)
    if t == "paragraph":
        cs = children(node)
        if len(cs) != 1 or cs[0].type != "inline":
            raise ValueError("paragraph without exactly one inline child")
        return render_inline(cs[0]) + "\n\n"
    if t == "heading":
        level = int((node.tag or "h1")[1:])
        cs = children(node)
        if len(cs) != 1 or cs[0].type != "inline":
            raise ValueError("heading without exactly one inline child")
        return ("=" * level) + " " + render_inline(cs[0]) + "\n\n"
    if t == "fence":
        return f"#raw({q(node.content or '')}, block: true)\n\n"
    if t == "blockquote":
        return "#quote(block: true)[\n" + render_flow(children(node)).strip() + "\n]\n\n"
    if t in {"bullet_list", "ordered_list"}:
        return list_items(node)
    if t == "list_item":
        return render_flow(children(node))
    if t == "hr":
        return "#line(length: 100%, stroke: 0.5pt + luma(78%))\n\n"
    if t == "table":
        cols, cells = table_cells(node)
        body = ",\n  ".join(cells)
        return (
            f"#table(columns: {cols}, inset: 4pt, stroke: 0.35pt + luma(78%),\n"
            f"  {body},\n)\n\n"
        )
    if t in {"thead", "tbody", "tr", "th", "td"}:
        return render_flow(children(node))
    raise ValueError(f"unsupported block token: {t}")


def walk(node: SyntaxTreeNode):
    yield node
    for child in children(node):
        yield from walk(child)


def source_visible_text(node: SyntaxTreeNode) -> str:
    """AST-derived text stream used only for a semantic-loss checksum."""
    if node.type in {"text", "code_inline", "fence"}:
        return node.content or ""
    return "".join(source_visible_text(c) for c in children(node))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="productions/ordivon-book-v0/book.mdx")
    ap.add_argument("--typst", default="out/book-portable/ordivon-book-v0.typ")
    ap.add_argument("--receipt", default="out/book-portable/projection-receipt.json")
    args = ap.parse_args()

    source = Path(args.source)
    raw = source.read_bytes()
    digest = sha256_bytes(raw)
    if digest != EXPECTED_SOURCE_SHA256:
        raise SystemExit(f"source digest drift: {digest} != {EXPECTED_SOURCE_SHA256}")
    text = raw.decode("utf-8")

    md = MarkdownIt("commonmark").enable("table")
    tokens = md.parse(text)
    root = SyntaxTreeNode(tokens)
    nodes = list(walk(root))
    unknown = sorted({n.type for n in nodes if n.type not in ALLOWED_BLOCK | ALLOWED_INLINE})
    if unknown:
        raise SystemExit(f"unsupported Markdown token types: {unknown}")

    token_counts = Counter(n.type for n in nodes)
    top_counts = Counter(t.type for t in tokens)
    visible = source_visible_text(root)
    body = render_block(root)
    preamble = f'''// Derived portable projection; source authority is {source.as_posix()}.
#set document(title: "Ordivon Book v0 - Finite Intelligence, Reality, and Revision")
#set page(paper: "a5", margin: (x: 17mm, y: 18mm), numbering: "1")
#set text(font: ("Noto Serif SC", "Microsoft YaHei"), size: 10.3pt, lang: "zh")
#set par(justify: true, leading: 0.72em)
#set heading(numbering: none)
#show raw: set text(font: ("DejaVu Sans Mono", "Noto Sans SC", "Microsoft YaHei"), size: 8.1pt)
#show quote: set block(inset: (left: 9pt), stroke: (left: 1pt + luma(70%)))

'''
    typst = Path(args.typst)
    typst.parent.mkdir(parents=True, exist_ok=True)
    typst_text = preamble + body
    typst.write_text(typst_text, encoding="utf-8")

    receipt = {
        "schemaVersion": 1,
        "kind": "ordivon.media-book-portable-projection",
        "truthRole": "derived-carrier-projection-not-book-semantic-authority",
        "source": {
            "path": source.as_posix(),
            "sha256": digest,
            "bytes": len(raw),
        },
        "parser": "markdown-it-py commonmark+table",
        "tokenCounts": dict(sorted(token_counts.items())),
        "topLevelTokenCounts": dict(sorted(top_counts.items())),
        "sourceVisibleTextSha256": sha256_bytes(visible.encode("utf-8")),
        "sourceVisibleTextCodepoints": len(visible),
        "typst": {
            "path": typst.as_posix(),
            "sha256": sha256_bytes(typst_text.encode("utf-8")),
            "bytes": len(typst_text.encode("utf-8")),
        },
        "boundaries": [
            "book.mdx remains semantic authority",
            "relative repository links retain visible label but are not emitted as false standalone-PDF destinations",
            "layout, pagination, font choice and line wrapping are carrier transformations",
            "portable rendering does not establish Human comprehension, preference, readership or public publication",
        ],
    }
    receipt_path = Path(args.receipt)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
