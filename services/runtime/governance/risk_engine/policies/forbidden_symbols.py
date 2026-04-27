from domains.research.models import AnalysisResult

FORBIDDEN_SYMBOLS = {"MEME", "DOGE", "PEPE", "SHIB"}


class ForbiddenSymbolsPolicy:
    """Policy to reject analyses on forbidden or highly-speculative symbols."""

    def check(self, analysis: AnalysisResult) -> list[str]:
        if not analysis.symbol:
            return []

        sym = analysis.symbol.upper()
        # Handle formats like BTC-USDT or BTC/USDT
        base_asset = sym.split("-")[0].split("/")[0]

        if base_asset in FORBIDDEN_SYMBOLS or "MEME" in sym:
            return [f"Asset {base_asset} (Symbol: {sym}) is blocked by ForbiddenSymbolsPolicy."]
        return []
