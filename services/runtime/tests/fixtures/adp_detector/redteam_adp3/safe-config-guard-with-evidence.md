# Safe: Config guard WITH invariant test evidence

The order placement capability is blocked by configuration guard.
This is verified by invariant test: test_can_place_live_order_must_be_false
and boundary evidence: paper_execution.py line 53 (environment="paper").
