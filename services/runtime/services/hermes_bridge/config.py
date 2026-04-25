"""PFIOS Hermes Bridge — config."""

from __future__ import annotations

import os

# Bridge identity
BRIDGE_NAME = "pfios-hermes-bridge"
BRIDGE_VERSION = "0.1.0"

# Server
BRIDGE_HOST = os.environ.get("PFIOS_BRIDGE_HOST", "127.0.0.1")
BRIDGE_PORT = int(os.environ.get("PFIOS_BRIDGE_PORT", "9120"))

# Auth — must match PFIOS_HERMES_API_TOKEN on the Ordivon side
BRIDGE_API_TOKEN = os.environ.get("PFIOS_BRIDGE_API_TOKEN", "")

# Model — defaults from hermes config; override via env
MODEL_PROVIDER = os.environ.get("PFIOS_BRIDGE_PROVIDER", "deepseek")
MODEL_NAME = os.environ.get("PFIOS_BRIDGE_MODEL", "deepseek-v4-pro")
MODEL_BASE_URL = os.environ.get("PFIOS_BRIDGE_BASE_URL", "https://api.deepseek.com")
MODEL_API_KEY = os.environ.get("PFIOS_BRIDGE_API_KEY", os.environ.get("DEEPSEEK_API_KEY", ""))

# Safety — hard block on dangerous modes
ALLOW_TOOLS = False
ALLOW_FILE_WRITE = False
ALLOW_SHELL = False
