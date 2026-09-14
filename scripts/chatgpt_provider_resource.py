#!/usr/bin/env python3
"""Canonical ChatGPT conversation resources for the current provider boundary."""

from __future__ import annotations
from urllib.parse import urlsplit

CHATGPT_ORIGIN = "https://chatgpt.com"


def _validate_conversation_id(conversation_id: str) -> str:
    if (
        not conversation_id
        or conversation_id.startswith("WEB:")
        or any(ch.isspace() or ch in "/?#" for ch in conversation_id)
    ):
        raise ValueError("ChatGPT provider resource contains an invalid conversation id")
    return conversation_id


def _canonical_origin_parts(value: str):
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError("ChatGPT provider resource must be one trimmed URI")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or parsed.hostname != "chatgpt.com":
        raise ValueError("ChatGPT provider resource must use https://chatgpt.com")
    if parsed.username is not None or parsed.password is not None or parsed.port is not None:
        raise ValueError("ChatGPT provider resource must use the canonical origin")
    return parsed, [part for part in parsed.path.split("/") if part]


def _conversation_id(value: str) -> str:
    _parsed, parts = _canonical_origin_parts(value)
    if len(parts) != 2 or parts[0] != "c":
        raise ValueError("ChatGPT provider resource must identify exactly one /c/<id> resource")
    return _validate_conversation_id(parts[1])


def _page_conversation_id(value: str) -> str:
    _parsed, parts = _canonical_origin_parts(value)
    if len(parts) < 2 or parts[-2] != "c":
        raise ValueError(
            "ChatGPT page URL does not identify one terminal /c/<id> conversation route"
        )
    return _validate_conversation_id(parts[-1])


def canonical_chatgpt_resource(value: str) -> str:
    return f"{CHATGPT_ORIGIN}/c/{_conversation_id(value)}"


def chatgpt_resource_from_page_url(url: str) -> str | None:
    try:
        return f"{CHATGPT_ORIGIN}/c/{_page_conversation_id(url)}"
    except (TypeError, ValueError):
        return None


def normalize_provider_resource(value: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(ch.isspace() for ch in value)
    ):
        raise ValueError("provider resource must be one trimmed absolute URI")
    parsed = urlsplit(value)
    if parsed.scheme == "chatgpt-conversation":
        raise ValueError("retired ChatGPT private resource scheme is unsupported")
    if parsed.scheme == "https" and parsed.hostname == "chatgpt.com":
        return canonical_chatgpt_resource(value)
    if not parsed.scheme:
        raise ValueError("provider resource must be an absolute URI")
    return value
