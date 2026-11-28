from __future__ import annotations

from html.parser import HTMLParser

from .constants import GAIN, REPO, WINDOWS


class TrendingParser(HTMLParser):
    """Collect one complete Box-row article at a time, not generic tag depth.

    HTML void elements (img/wbr/br/etc.) do not emit end tags, so counting
    every HTML start/end as a balanced pair silently drops Trending cards.
    """
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.article_depth = 0
        self.h2_depth = 0
        self.hrefs: list[str] = []
        self.bits: list[str] = []
        self.results: list[dict] = []
        self.unparseable_cards = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "article":
            if self.article_depth:
                self.article_depth += 1
                return
            if "Box-row" in a.get("class", "").split():
                self.article_depth = 1
                self.h2_depth = 0
                self.hrefs, self.bits = [], []
            return
        if not self.article_depth:
            return
        if tag == "h2":
            self.h2_depth += 1
        elif tag == "a" and self.h2_depth:
            self.hrefs.append(a.get("href", ""))

    def handle_endtag(self, tag):
        if not self.article_depth:
            return
        if tag == "article":
            self.article_depth -= 1
            if not self.article_depth:
                self._finish_card()
            return
        if tag == "h2" and self.h2_depth:
            self.h2_depth -= 1

    def _finish_card(self):
        repo = next((v.strip("/") for v in self.hrefs
                     if REPO.fullmatch(v.strip("/"))), None)
        if not repo:
            self.unparseable_cards += 1
            return
        desc = " ".join("".join(self.bits).split())
        match = GAIN.search(desc)
        self.results.append({
            "repo": repo,
            "newStars": int(match.group(1).replace(",", "")) if match else None,
            "sourceWindowLabel": match.group(2).lower() if match else None,
        })

    def handle_data(self, text):
        if self.article_depth:
            self.bits.append(text)


def parse_trending(html: str, window: str) -> list[dict]:
    if window not in WINDOWS:
        raise ValueError("unknown Trending window")
    parser = TrendingParser()
    parser.feed(html)
    parser.close()
    if parser.article_depth:
        raise ValueError("unterminated GitHub Trending article; source window unverified")
    if parser.unparseable_cards:
        raise ValueError("unparseable GitHub Trending article; source window unverified")
    if not parser.results:
        raise ValueError("GitHub Trending article markup missing; cannot silently fall back")
    return [{"repo": e["repo"], "newStars": e["newStars"],
             "sourceWindowLabel": e["sourceWindowLabel"] if e["sourceWindowLabel"] == WINDOWS[window] else None}
            for e in parser.results]
