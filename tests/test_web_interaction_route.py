from __future__ import annotations
import sys
import unittest
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import web_interaction_route as R

AVAILABLE={
 'native_connector':{'state':'caller_bound','reason':'x'},
 'direct_http':{'state':'available','reason':'x'},
 'firecrawl':{'state':'unavailable','reason':'x'},
 'playwright':{'state':'task_local','reason':'x'},
 'browser_use':{'state':'available','reason':'x'},
 'computer_use':{'state':'caller_bound','reason':'x'},
}

class WebInteractionRouteTests(unittest.TestCase):
 def resolve(self, needs, caller=()):
  with mock.patch.object(R,'census',return_value=AVAILABLE): return R.resolve(needs,caller_available=caller)

 def test_plain_read_uses_http_not_browser(self):
  d=self.resolve(R.TaskNeeds()); self.assertEqual(d['selectedRoute'],'direct_http')

 def test_native_connector_precedes_other_routes_when_caller_proves_it(self):
  d=self.resolve(R.TaskNeeds(native_provider_available=True),('native_connector',)); self.assertEqual(d['selectedRoute'],'native_connector')

 def test_site_scale_prefers_firecrawl_only_when_actually_available(self):
  a=dict(AVAILABLE); a['firecrawl']={'state':'available','reason':'x'}
  with mock.patch.object(R,'census',return_value=a): d=R.resolve(R.TaskNeeds(site_scale_web_acquisition=True))
  self.assertEqual(d['selectedRoute'],'firecrawl')

 def test_studied_but_unavailable_firecrawl_does_not_silently_shrink_site_scale_task(self):
  d=self.resolve(R.TaskNeeds(site_scale_web_acquisition=True)); self.assertIsNone(d['selectedRoute']); self.assertEqual(d['standing'],'NO_ADMITTED_PROVIDER')
  self.assertEqual(d['considered'][0]['route'],'firecrawl'); self.assertEqual(d['considered'][0]['standing'],'not_available')

 def test_known_browser_flow_uses_caller_admitted_playwright(self):
  d=self.resolve(R.TaskNeeds(requires_interaction=True,deterministic_browser_flow=True),('playwright',)); self.assertEqual(d['selectedRoute'],'playwright')

 def test_known_browser_flow_falls_to_browser_use_without_generic_playwright(self):
  d=self.resolve(R.TaskNeeds(requires_interaction=True,deterministic_browser_flow=True)); self.assertEqual(d['selectedRoute'],'browser_use')

 def test_unknown_interactive_browser_uses_browser_use(self):
  d=self.resolve(R.TaskNeeds(requires_interaction=True,adaptive_browser_reasoning=True)); self.assertEqual(d['selectedRoute'],'browser_use')

 def test_desktop_requires_explicit_caller_capability(self):
  needs=R.TaskNeeds(requires_interaction=True,requires_desktop_gui=True)
  d=self.resolve(needs); self.assertEqual(d['standing'],'NO_ADMITTED_PROVIDER')
  d=self.resolve(needs,('computer_use',)); self.assertEqual(d['selectedRoute'],'computer_use')

 def test_invalid_mixed_browser_semantics_rejected(self):
  with self.assertRaises(ValueError): R.TaskNeeds(requires_interaction=True,deterministic_browser_flow=True,adaptive_browser_reasoning=True)

 def test_caller_cannot_invent_browser_use_availability(self):
  with self.assertRaises(ValueError): self.resolve(R.TaskNeeds(),('browser_use',))

if __name__=='__main__': unittest.main()
