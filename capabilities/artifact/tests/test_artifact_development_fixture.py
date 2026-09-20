from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROFILE=ROOT/'artifact-delivery/examples/presentation-local-development-r1.json'
SOURCE=ROOT/'artifact-delivery/examples/presentation-local-development-source-r1.json'
REQUEST=ROOT/'artifact-delivery/examples/presentation-local-development-request-r1.json'
BASE_SOURCE=ROOT/'artifact-delivery/examples/presentation-native-smoke-source-r1.json'

class ArtifactDevelopmentFixtureTests(unittest.TestCase):
    def test_profile_is_explicitly_non_release(self)->None:
        profile=json.loads(PROFILE.read_text())
        self.assertEqual(profile['id'],'presentation-local-development-r1')
        self.assertEqual(profile['deliveryTargets'],['local-development-only'])
        self.assertFalse(profile['targetRenderer']['required'])
        self.assertNotIn('companions',profile)
        self.assertEqual({k for k,v in profile['gates'].items() if v},{'profileSchema','structural','semantic'})
        self.assertIn('DEVELOPMENT-ONLY',profile['notes'])
        self.assertIn('does not claim target rendering',profile['notes'])

    def test_source_changes_only_acceptance_binding_and_note(self)->None:
        source=json.loads(SOURCE.read_text()); base=json.loads(BASE_SOURCE.read_text())
        self.assertEqual(source['profileId'],'presentation-local-development-r1')
        base['profileId']=source['profileId']; base['notes']=source['notes']
        self.assertEqual(source,base)

    def test_request_binds_exact_profile_and_source(self)->None:
        request=json.loads(REQUEST.read_text())
        self.assertEqual(request['profile']['sha256'],hashlib.sha256(PROFILE.read_bytes()).hexdigest())
        self.assertEqual(request['source']['sha256'],hashlib.sha256(SOURCE.read_bytes()).hexdigest())
        self.assertEqual(request['profile']['id'],'presentation-local-development-r1')
        self.assertEqual(request['source']['path'],SOURCE.name)
        self.assertIn('Development-only',request['notes'])
