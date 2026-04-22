from packs.finance.policy import finance_trading_limits_policy_path, get_finance_policy_overlays
from packs.finance.tool_refs import get_finance_tool_refs


def test_finance_pack_policy_overlay_refs_point_to_trading_limits():
    overlays = get_finance_policy_overlays()

    assert overlays[0].policy_id == "finance.trading_limits"
    assert overlays[0].path == finance_trading_limits_policy_path()
    assert overlays[0].path.name == "trading_limits.yaml"


def test_finance_pack_tool_refs_catalog_known_finance_tool_namespaces():
    refs = get_finance_tool_refs()

    assert refs.market_data == ("tools.market_data",)
    assert refs.news_data == ("tools.news_data",)
    assert refs.broker == ("tools.broker",)
