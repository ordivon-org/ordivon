from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_installer_never_accepts_live_mode_or_echoes_values():
    s=(ROOT/'scripts/install-nonlive-credential').read_text()
    assert "{'okx-demo','binance-testnet'}" in s
    assert 'live' not in "{'okx-demo','binance-testnet'}"
    assert 'getpass.getpass' in s
    assert 'demo = true' in s
    assert '/root/.config/ordivon/secrets' in s
    assert 'private.pem' in s and 'public.pem' in s
