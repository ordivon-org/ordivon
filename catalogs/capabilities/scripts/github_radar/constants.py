from __future__ import annotations

import re

WINDOWS = {"daily": "today", "weekly": "this week", "monthly": "this month"}
GH = "https://github.com"
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
GAIN = re.compile(r"([0-9][0-9,]*)\s+stars?\s+(today|this week|this month)", re.IGNORECASE)
