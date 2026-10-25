"""PG exact conversation owner selection is fail-closed before a consumer read."""
from __future__ import annotations
import sys
import types
from pathlib import Path
from types import SimpleNamespace
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from agent_automation_browserless import BrowserlessAutomationService  # noqa: E402


def test_pg_owner_must_seal_legacy_before_use(monkeypatch, tmp_path):
    seen=[]
    fake=types.ModuleType("postgres_conversation_binding")
    class ProofPG:
        def __init__(self,dsn):
            seen.append(("init",dsn))
        def assert_legacy_sealed(self,path,*,fresh_bootstrap):
            seen.append(("seal",path,fresh_bootstrap))
    fake.PostgresConversationBindingStore=ProofPG
    monkeypatch.setitem(sys.modules,"postgres_conversation_binding",fake)
    monkeypatch.setenv("ORDIVON_CONVERSATION_POSTGRES_DSN","host=disposable-pg")
    monkeypatch.delenv("ORDIVON_CONVERSATION_PG_FRESH_BOOTSTRAP",raising=False)
    service=object.__new__(BrowserlessAutomationService)
    service.config=SimpleNamespace(ledger=tmp_path/"legacy.sqlite")
    owner=service._postgres_conversation_owner()
    assert isinstance(owner,ProofPG)
    assert seen==[("init","host=disposable-pg"),("seal",tmp_path/"legacy.sqlite",False)]


def test_pg_owner_refuses_unsealed_source(monkeypatch,tmp_path):
    fake=types.ModuleType("postgres_conversation_binding")
    class Unsealed:
        def __init__(self,dsn):
            pass
        def assert_legacy_sealed(self,*args,**kwargs):
            raise RuntimeError("unsealed")
    fake.PostgresConversationBindingStore=Unsealed
    monkeypatch.setitem(sys.modules,"postgres_conversation_binding",fake)
    monkeypatch.setenv("ORDIVON_CONVERSATION_POSTGRES_DSN","host=disposable-pg")
    service=object.__new__(BrowserlessAutomationService)
    service.config=SimpleNamespace(ledger=tmp_path/"legacy.sqlite")
    with pytest.raises(RuntimeError,match="unsealed"):
        service._postgres_conversation_owner()
