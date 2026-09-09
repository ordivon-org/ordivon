from __future__ import annotations

import inspect
import unittest

from ordivon_harness.loop_driver import HarnessLoopDriverIdentity
from ordivon_harness.standalone import StandaloneHarnessRunner


class AM8LiveMorphingGateTests(unittest.TestCase):
    def test_no_live_loop_install_or_factory_surface_is_exposed(self) -> None:
        params = inspect.signature(StandaloneHarnessRunner.__init__).parameters
        for forbidden in (
            "loop_driver_binding",
            "loop_factory",
            "plugin_registry",
            "hot_reload",
        ):
            self.assertNotIn(forbidden, params)
        for forbidden in ("factory", "build", "install", "unload", "reload"):
            self.assertFalse(hasattr(HarnessLoopDriverIdentity, forbidden))


if __name__ == "__main__":
    unittest.main()
