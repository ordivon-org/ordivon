import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('artifact_profile_v2',ROOT/'scripts/artifact_profile_v2.py')
MODULE=importlib.util.module_from_spec(SPEC); assert SPEC.loader is not None; SPEC.loader.exec_module(MODULE)


class ArtifactProfileV2Tests(unittest.TestCase):
    def production_profiles(self):
        out=[]
        for p in sorted((ROOT/'artifact-delivery/examples').glob('*.json')):
            try: x=json.loads(p.read_text())
            except Exception: continue
            if x.get('profileVersion')==1 and 'artifactClass' in x: out.append((p,x))
        return out

    def test_all_v1_semantic_fields_are_preserved_by_mapping(self):
        for p,source in self.production_profiles():
            mapped=MODULE.map_v1(source)
            self.assertEqual(mapped['id'],source['id'],p.name)
            self.assertEqual(mapped['construction']['authorityMode'],source['authorityMode'],p.name)
            self.assertEqual(mapped['construction']['locale'],source['locale'],p.name)
            outs=[]
            for o in mapped['outputs']:
                outs.append({k:o[k] for k in ('role','purpose','required') if k in o} | {'format':o['format']['name']} | ({'editable':o['editable']} if 'editable' in o else {}))
            source_out=[{'role':'primary','format':source['primaryOutput']['format'],'purpose':source['primaryOutput']['purpose'],'required':source['primaryOutput']['required']} | ({'editable':source['primaryOutput']['editable']} if 'editable' in source['primaryOutput'] else {})]
            for o in source.get('companions',[]):
                source_out.append({'role':'companion','format':o['format'],'purpose':o['purpose'],'required':o['required']} | ({'editable':o['editable']} if 'editable' in o else {}))
            self.assertEqual(outs,source_out,p.name)
            targets=[{'name':x['name'],'platform':x.get('platform'),'required':x['required']} for x in mapped.get('targetAuthorities',[]) if x['authorityClass']=='native-consumer']
            source_targets=[]
            if source.get('targetRenderer'):
                r=source['targetRenderer']; source_targets.append({'name':r['name'],'platform':r['platform'],'required':r['required']})
            for r in source.get('secondaryRenderers',[]): source_targets.append({'name':r['name'],'platform':r['platform'],'required':r['required']})
            self.assertEqual(targets,source_targets,p.name)
            self.assertEqual({k:v['required'] for k,v in mapped['requiredEvidence'].items()},source['gates'],p.name)
            self.assertEqual(mapped['deliveryDefaults']['targets'],source['deliveryTargets'],p.name)
            self.assertEqual(mapped['notes'],source.get('notes',''),p.name)
            pp=mapped.get('profilePolicy',{})
            if source.get('unsupportedRenderers'): self.assertEqual(pp['unsupportedTargets'],source['unsupportedRenderers'],p.name)
            for key in ('aspectRatio','fontPolicy','fonts','semanticPolicy','renderEvidence'):
                if key in source: self.assertEqual(pp['presentation'][key],source[key],f"{p.name}:{key}")
            if 'conformancePolicy' in source: self.assertEqual(pp['conformance'],source['conformancePolicy'],p.name)

    def test_shadow_profile_semantics_are_preserved_by_mapping(self):
        for p in sorted((ROOT/'artifact-delivery/shadow-profiles').glob('*.json')):
            source=json.loads(p.read_text()); mapped=MODULE.map_shadow(source); c=source['classification']
            self.assertEqual(mapped['classification']['family'],c['family'],p.name)
            self.assertEqual(mapped['classification']['representation'],c['representation'],p.name)
            self.assertEqual(mapped['classification']['format']['name'],c['format'],p.name)
            self.assertEqual(mapped['classification']['format'].get('mediaType'),c.get('mediaType'),p.name)
            self.assertEqual(mapped['classification']['purposes'],c['purpose'],p.name)
            self.assertEqual(mapped['profilePolicy']['formatPolicy'],source['formatPolicy'],p.name)
            self.assertEqual(mapped['nonClaims'],source['nonClaims'],p.name)
            if 'objectContract' in source:
                self.assertEqual(mapped.get('objectContract'),source['objectContract'],p.name)
            for name,value in source['requiredEvidence'].items():
                got=mapped['requiredEvidence'][name]
                self.assertEqual(got['required'],value['required'],f"{p.name}:{name}")
                self.assertEqual(got['claim'],value['claim'],f"{p.name}:{name}")
                params={k:v for k,v in value.items() if k not in {'required','claim'}}
                self.assertEqual(got.get('parameters',{}),params,f"{p.name}:{name}")

    def test_all_current_production_profiles_map_and_validate(self):
        profiles=self.production_profiles()
        self.assertGreaterEqual(len(profiles),8)
        for p,source in profiles:
            mapped=MODULE.map_profile(source)
            self.assertEqual(MODULE.validate(mapped),[],p.name)
            self.assertEqual(sum(1 for o in mapped['outputs'] if o['role']=='primary'),1)
            self.assertNotIn('artifactClass',mapped)

    def test_legacy_accessible_is_profile_purpose_not_family(self):
        source=json.loads((ROOT/'artifact-delivery/examples/pdf-accessible-r1.json').read_text())
        mapped=MODULE.map_v1(source)
        self.assertEqual(mapped['classification']['family'],'fixed-document')
        self.assertEqual(mapped['classification']['representation'],'fixed-layout')
        self.assertEqual(mapped['classification']['conformanceProfile'],'PDF/UA-2')
        self.assertIn('accessibility',mapped['classification']['purposes'])

    def test_legacy_gate_truth_values_are_preserved_as_evidence_requirements(self):
        source=json.loads((ROOT/'artifact-delivery/examples/presentation-local-development-r1.json').read_text())
        mapped=MODULE.map_v1(source)
        for k,v in source['gates'].items(): self.assertEqual(mapped['requiredEvidence'][k]['required'],v)
        self.assertFalse(mapped['requiredEvidence']['visual']['required'])
        self.assertFalse(mapped['requiredEvidence']['target']['required'])

    def test_presentation_specific_fields_do_not_enter_core_classification(self):
        source=json.loads((ROOT/'artifact-delivery/examples/presentation-ultrawide-34x10-r1.json').read_text())
        mapped=MODULE.map_v1(source)
        self.assertEqual(mapped['classification']['family'],'presentation')
        self.assertNotIn('aspectRatio',mapped['classification'])
        self.assertEqual(mapped['profilePolicy']['presentation']['aspectRatio'],'34:10')
        self.assertIn('fonts',mapped['profilePolicy']['presentation'])

    def test_shadow_required_evidence_has_explicit_claims(self):
        for p in sorted((ROOT/'artifact-delivery/shadow-profiles').glob('*.json')):
            source=json.loads(p.read_text())
            for name,value in source.get('requiredEvidence',{}).items():
                self.assertIn('claim',value,f"{p.name}:{name}")
                self.assertTrue(value['claim'].strip(),f"{p.name}:{name}")

    def test_still_image_shadow_maps_without_object_contract(self):
        source=json.loads((ROOT/'artifact-delivery/shadow-profiles/still-image-png-srgb-r1.json').read_text())
        mapped=MODULE.map_shadow(source)
        self.assertEqual(MODULE.validate(mapped),[])
        self.assertEqual(mapped['classification']['family'],'still-image')
        self.assertNotIn('objectContract',mapped)
        self.assertEqual(mapped['targetAuthorities'][0]['authorityClass'],'independent-implementation-matrix')

    def test_static_svg_shadow_maps_as_still_image_without_object_contract(self):
        source=json.loads((ROOT/'artifact-delivery/shadow-profiles/still-image-svg-static-r1.json').read_text())
        mapped=MODULE.map_shadow(source)
        self.assertEqual(MODULE.validate(mapped),[])
        self.assertEqual(mapped['classification']['family'],'still-image')
        self.assertEqual(mapped['classification']['format']['mediaType'],'image/svg+xml')
        self.assertNotIn('objectContract',mapped)
        self.assertEqual(mapped['targetAuthorities'][0]['authorityClass'],'independent-implementation-matrix')

    def test_dataset_shadow_requires_separate_object_contract(self):
        source=json.loads((ROOT/'artifact-delivery/shadow-profiles/dataset-parquet-flat-r1.json').read_text())
        mapped=MODULE.map_shadow(source)
        self.assertEqual(MODULE.validate(mapped),[])
        self.assertEqual(mapped['classification']['family'],'dataset')
        self.assertTrue(mapped['objectContract']['required'])
        self.assertEqual(mapped['objectContract']['binding'],'request-digest')
        self.assertEqual(mapped['classification']['format']['mediaType'],'application/vnd.apache.parquet')

    def test_message_shadow_maps_parser_matrix_and_message_contract(self):
        source=json.loads((ROOT/'artifact-delivery/shadow-profiles/message-internet-text-r1.json').read_text())
        mapped=MODULE.map_shadow(source)
        self.assertEqual(MODULE.validate(mapped),[])
        self.assertEqual(mapped['classification']['family'],'message')
        self.assertEqual(mapped['classification']['format']['mediaType'],'message/rfc822')
        self.assertEqual(mapped['objectContract'],source['objectContract'])
        self.assertEqual(mapped['targetAuthorities'][0]['authorityClass'],'independent-implementation-matrix')

    def test_web_archive_shadow_maps_parser_matrix_and_capture_contract(self):
        source=json.loads((ROOT/'artifact-delivery/shadow-profiles/web-archive-warc-response-r1.json').read_text())
        mapped=MODULE.map_shadow(source)
        self.assertEqual(MODULE.validate(mapped),[])
        self.assertEqual(mapped['classification']['family'],'web-archive')
        self.assertEqual(mapped['classification']['format']['mediaType'],'application/warc')
        self.assertEqual(mapped['objectContract'],source['objectContract'])
        self.assertEqual(mapped['targetAuthorities'][0]['authorityClass'],'independent-implementation-matrix')

    def test_design2d_aseprite_shadow_maps_native_exporter_and_object_contract(self):
        source=json.loads((ROOT/'artifact-delivery/shadow-profiles/design-2d-aseprite-horizontal-sheet-r1.json').read_text())
        mapped=MODULE.map_shadow(source)
        self.assertEqual(MODULE.validate(mapped),[])
        self.assertEqual(mapped['classification']['family'],'design-2d')
        self.assertEqual(mapped['classification']['format']['name'],'Aseprite (.ase/.aseprite)')
        self.assertEqual(mapped['objectContract'],source['objectContract'])
        self.assertEqual(mapped['targetAuthorities'][0]['authorityClass'],'native-consumer')

    def test_design2d_tiled_shadow_maps_native_authority_and_object_contract(self):
        source=json.loads((ROOT/'artifact-delivery/shadow-profiles/design-2d-tiled-tmj-object-map-r1.json').read_text())
        mapped=MODULE.map_shadow(source)
        self.assertEqual(MODULE.validate(mapped),[])
        self.assertEqual(mapped['classification']['family'],'design-2d')
        self.assertEqual(mapped['classification']['format']['name'],'Tiled JSON Map (TMJ)')
        self.assertEqual(mapped['objectContract'],source['objectContract'])
        self.assertEqual(mapped['targetAuthorities'][0]['authorityClass'],'native-consumer')

    def test_design3d_shadow_maps_standard_validator_and_scene_contract(self):
        source=json.loads((ROOT/'artifact-delivery/shadow-profiles/design-3d-glb-static-mesh-r1.json').read_text())
        mapped=MODULE.map_shadow(source)
        self.assertEqual(MODULE.validate(mapped),[])
        self.assertEqual(mapped['classification']['family'],'design-3d')
        self.assertEqual(mapped['classification']['format']['mediaType'],'model/gltf-binary')
        self.assertEqual(mapped['objectContract'],source['objectContract'])
        self.assertEqual(mapped['targetAuthorities'][0]['authorityClass'],'standard-validator')

    def test_software_release_shadow_maps_implementation_matrix_and_release_contract(self):
        source=json.loads((ROOT/'artifact-delivery/shadow-profiles/software-release-oci-image-r1.json').read_text())
        mapped=MODULE.map_shadow(source)
        self.assertEqual(MODULE.validate(mapped),[])
        self.assertEqual(mapped['classification']['family'],'software-release')
        self.assertEqual(mapped['classification']['format']['mediaType'],'application/vnd.oci.image.manifest.v1+json')
        self.assertEqual(mapped['objectContract'],source['objectContract'])
        self.assertEqual(mapped['targetAuthorities'][0]['authorityClass'],'independent-implementation-matrix')

    def test_linux_elf_release_shadow_maps_tool_matrix_and_release_contract(self):
        source=json.loads((ROOT/'artifact-delivery/shadow-profiles/software-release-linux-elf-executable-r1.json').read_text())
        mapped=MODULE.map_shadow(source)
        self.assertEqual(MODULE.validate(mapped),[])
        self.assertEqual(mapped['classification']['family'],'software-release')
        self.assertEqual(mapped['classification']['format']['mediaType'],'application/vnd.elf')
        self.assertEqual(mapped['objectContract'],source['objectContract'])
        self.assertEqual(mapped['targetAuthorities'][0]['authorityClass'],'independent-implementation-matrix')

    def test_moving_image_shadow_maps_standard_validator_and_decoded_content_contract(self):
        source=json.loads((ROOT/'artifact-delivery/shadow-profiles/moving-image-matroska-ffv1-v3-r1.json').read_text())
        mapped=MODULE.map_shadow(source)
        self.assertEqual(MODULE.validate(mapped),[])
        self.assertEqual(mapped['classification']['family'],'moving-image')
        self.assertEqual(mapped['classification']['format']['mediaType'],'video/matroska')
        self.assertEqual(mapped['objectContract'],source['objectContract'])
        self.assertEqual(mapped['targetAuthorities'][0]['authorityClass'],'standard-validator')

    def test_audio_shadow_maps_decoder_matrix_and_generic_object_contract(self):
        source=json.loads((ROOT/'artifact-delivery/shadow-profiles/audio-flac-pcm16-r1.json').read_text())
        mapped=MODULE.map_shadow(source)
        self.assertEqual(MODULE.validate(mapped),[])
        self.assertEqual(mapped['classification']['family'],'audio')
        self.assertEqual(mapped['classification']['format']['mediaType'],'audio/flac')
        self.assertEqual(mapped['objectContract'],source['objectContract'])
        self.assertEqual(mapped['targetAuthorities'][0]['authorityClass'],'independent-implementation-matrix')
        self.assertGreaterEqual(mapped['targetAuthorities'][0]['minimumIndependentImplementations'],2)

    def test_wave_audio_shadow_maps_decoder_matrix_and_separate_profile_contract(self):
        source=json.loads((ROOT/'artifact-delivery/shadow-profiles/audio-wave-pcm16-r1.json').read_text())
        mapped=MODULE.map_shadow(source)
        self.assertEqual(MODULE.validate(mapped),[])
        self.assertEqual(mapped['classification']['family'],'audio')
        self.assertEqual(mapped['classification']['format']['mediaType'],'audio/vnd.wave')
        self.assertEqual(mapped['objectContract'],source['objectContract'])
        self.assertEqual(mapped['targetAuthorities'][0]['authorityClass'],'independent-implementation-matrix')

    def test_ogg_vorbis_audio_shadow_maps_browser_decoder_matrix_and_contract(self):
        source=json.loads((ROOT/'artifact-delivery/shadow-profiles/audio-ogg-vorbis-r1.json').read_text())
        mapped=MODULE.map_shadow(source)
        self.assertEqual(MODULE.validate(mapped),[])
        self.assertEqual(mapped['classification']['family'],'audio')
        self.assertEqual(mapped['classification']['format']['mediaType'],'audio/ogg')
        self.assertEqual(mapped['objectContract'],source['objectContract'])
        self.assertEqual(mapped['targetAuthorities'][0]['authorityClass'],'independent-implementation-matrix')
        self.assertGreaterEqual(mapped['targetAuthorities'][0]['minimumIndependentImplementations'],2)

    def test_geospatial_shadow_maps_standard_validator_and_generic_object_contract(self):
        source=json.loads((ROOT/'artifact-delivery/shadow-profiles/geospatial-geopackage-point-r1.json').read_text())
        mapped=MODULE.map_shadow(source)
        self.assertEqual(MODULE.validate(mapped),[])
        self.assertEqual(mapped['classification']['family'],'geospatial')
        self.assertEqual(mapped['classification']['format']['mediaType'],'application/geopackage+sqlite3')
        self.assertEqual(mapped['objectContract'],source['objectContract'])
        self.assertEqual(mapped['targetAuthorities'][0]['authorityClass'],'standard-validator')

    def test_schema_rejects_old_category_error_as_family(self):
        source=json.loads((ROOT/'artifact-delivery/shadow-profiles/still-image-png-srgb-r1.json').read_text())
        mapped=MODULE.map_shadow(source); mapped['classification']['family']='accessible'
        failures=MODULE.validate(mapped)
        self.assertTrue(any('not one of' in f for f in failures),failures)

    def test_semantic_validator_requires_exactly_one_primary_output(self):
        source=json.loads((ROOT/'artifact-delivery/shadow-profiles/still-image-png-srgb-r1.json').read_text())
        mapped=MODULE.map_shadow(source); mapped['outputs'].append(dict(mapped['outputs'][0]))
        failures=MODULE.validate(mapped)
        self.assertTrue(any('exactly one primary output' in f for f in failures),failures)

    def test_required_object_contract_must_name_schema(self):
        source=json.loads((ROOT/'artifact-delivery/shadow-profiles/dataset-parquet-flat-r1.json').read_text())
        mapped=MODULE.map_shadow(source); mapped['objectContract'].pop('schemaReference')
        failures=MODULE.validate(mapped)
        self.assertIn('required objectContract must declare schemaReference',failures)


if __name__=='__main__': unittest.main()
