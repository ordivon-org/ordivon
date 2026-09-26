from __future__ import annotations

from ordivon_capital.markets.us_treasury_rates import compose_capture, parse_feed, NOMINAL_FIELDS, REAL_FIELDS

NOMINAL = '''<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom" xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices" xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"><updated>2026-09-24T02:02:11Z</updated><entry><content type="application/xml"><m:properties><d:NEW_DATE>2026-09-22T00:00:00</d:NEW_DATE><d:BC_2YEAR>4.71</d:BC_2YEAR><d:BC_5YEAR>4.83</d:BC_5YEAR><d:BC_10YEAR>4.96</d:BC_10YEAR><d:BC_20YEAR>5.33</d:BC_20YEAR><d:BC_30YEAR>5.29</d:BC_30YEAR></m:properties></content></entry><entry><content type="application/xml"><m:properties><d:NEW_DATE>2026-09-23T00:00:00</d:NEW_DATE><d:BC_2YEAR>4.85</d:BC_2YEAR><d:BC_5YEAR>4.99</d:BC_5YEAR><d:BC_10YEAR>5.11</d:BC_10YEAR><d:BC_20YEAR>5.45</d:BC_20YEAR><d:BC_30YEAR>5.40</d:BC_30YEAR></m:properties></content></entry></feed>'''
REAL = '''<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom" xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices" xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"><updated>2026-09-24T02:02:11Z</updated><entry><content type="application/xml"><m:properties><d:NEW_DATE>2026-09-22T00:00:00</d:NEW_DATE><d:TC_5YEAR>2.51</d:TC_5YEAR><d:TC_7YEAR>2.56</d:TC_7YEAR><d:TC_10YEAR>2.63</d:TC_10YEAR><d:TC_20YEAR>2.88</d:TC_20YEAR><d:TC_30YEAR>3.04</d:TC_30YEAR></m:properties></content></entry><entry><content type="application/xml"><m:properties><d:NEW_DATE>2026-09-23T00:00:00</d:NEW_DATE><d:TC_5YEAR>2.65</d:TC_5YEAR><d:TC_7YEAR>2.70</d:TC_7YEAR><d:TC_10YEAR>2.76</d:TC_10YEAR><d:TC_20YEAR>2.99</d:TC_20YEAR><d:TC_30YEAR>3.14</d:TC_30YEAR></m:properties></content></entry></feed>'''


def test_parse_treasury_atom_feed():
    nominal = parse_feed(NOMINAL, NOMINAL_FIELDS)
    real = parse_feed(REAL, REAL_FIELDS)
    assert nominal["rows"]["2026-09-23"]["10y"] == "5.11"
    assert real["rows"]["2026-09-23"]["10y"] == "2.76"


def test_compose_capture_derives_changes_and_same_maturity_spread():
    result = compose_capture(nominal_xml=NOMINAL, real_xml=REAL, observed_at_ms=123)
    assert result["latestCommonDate"] == "2026-09-23"
    assert result["previousCommonDate"] == "2026-09-22"
    assert result["latest"]["nominalParYieldPct"]["10y"] == "5.11"
    assert result["latest"]["realParYieldPct"]["10y"] == "2.76"
    assert result["latest"]["nominalMinusRealPct"]["10y"] == "2.35"
    assert result["changeBp"]["nominal"]["10y"] == "15.00"
    assert result["changeBp"]["real"]["10y"] == "13.00"
    assert result["changeBp"]["nominalMinusReal"]["10y"] == "2.00"
    assert result["latest"]["nominalCurveSlopes"]["2s10sBp"] == "26.00"
    assert result["externalFinancialWriteAttempted"] is False
