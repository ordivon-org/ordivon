from pydantic import BaseModel
from typing import List

class AnalyzeRequest(BaseModel):
    query: str
    symbols: List[str] = []
    timeframe: str | None = "1h"
    context_mode: str = "standard"
    workflow: str = "analyze_and_suggest"
