from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_local_handoff_is_admission_only_and_sanitizes_raw_data():
    s=(ROOT/'scripts/run-live-test-admission-local').read_text()
    assert 'order.place' not in s
    assert 'placeOrder' not in s
    assert 'externalFinancialWriteAttempted' in s
    assert 'rm -f "$raw"' in s
    assert 'quoteBalanceLe1' in s
    assert 'withdrawPermission' in s
    assert 'tradePermission' in s
