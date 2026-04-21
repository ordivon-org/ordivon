# Tools

`tools/` contains atomic integrations with the outside world: market feeds, news, storage, notifications, brokers, and export utilities.

Tools should be composable and narrow. If something starts mixing prompt logic, governance checks, and persistence side effects, it is no longer a tool.
