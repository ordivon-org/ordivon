from __future__ import annotations
import datetime as dt
import importlib.util
import json
import tempfile
import unittest
import urllib.parse
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('r2mail',ROOT/'scripts/artifact_r2_mailbox.py')
M=importlib.util.module_from_spec(SPEC);assert SPEC and SPEC.loader;SPEC.loader.exec_module(M)

class ArtifactR2MailboxTests(unittest.TestCase):
    def test_content_descriptor_and_object_key_are_digest_addressed(self):
        d=M.content_descriptor(b'hello','application/octet-stream')
        self.assertEqual(d,{'mediaType':'application/octet-stream','digest':'sha256:2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824','size':5})
        self.assertEqual(M.object_key(d),'objects/sha256/2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824')

    def test_exact_verification_rejects_partial_wrong_digest_and_oversize(self):
        d=M.content_descriptor(b'abc','application/octet-stream')
        with self.assertRaisesRegex(ValueError,'size mismatch'):M.verify_exact_bytes(b'ab',d)
        bad=dict(d);bad['digest']='sha256:'+'0'*64
        with self.assertRaisesRegex(ValueError,'sha256 mismatch'):M.verify_exact_bytes(b'abc',bad)
        with self.assertRaisesRegex(ValueError,'maximum'):M.validate_descriptor({'mediaType':'application/octet-stream','digest':d['digest'],'size':M.DEFAULT_MAX_BYTES+1})

    def test_ambiguous_retry_reconciles_exact_existing_and_never_overwrites_conflict(self):
        data=b'abc';d=M.content_descriptor(data,'application/octet-stream')
        self.assertEqual(M.reconcile_existing(None,data,d)['standing'],'CREATE_ALLOWED')
        self.assertEqual(M.reconcile_existing(data,data,d)['standing'],'RECOVERED_EXISTING')
        self.assertEqual(M.reconcile_existing(b'xxx',data,d)['standing'],'CORRUPT_CONFLICT')

    def test_temp_credential_request_is_single_object_and_bounded(self):
        key='objects/sha256/'+'a'*64
        r=M.temp_credential_request(bucket='mailbox',parent_access_key_id='parent',key=key,permission='object-read-write',ttl_seconds=300)
        self.assertEqual(r['objects'],[key]);self.assertEqual(r['ttlSeconds'],300)
        with self.assertRaises(ValueError):M.temp_credential_request(bucket='mailbox',parent_access_key_id='parent',key=key,permission='object-read-write',ttl_seconds=901)

    def test_aws_official_sigv4_query_example_matches_signature(self):
        url=M.sigv4_presign(method='GET',url='https://examplebucket.s3.amazonaws.com/test.txt',access_key_id='AKIAIOSFODNN7EXAMPLE',secret_access_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',region='us-east-1',expires_seconds=86400,timestamp=dt.datetime(2013,5,24,tzinfo=dt.timezone.utc))
        q=dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))
        self.assertEqual(q['X-Amz-Signature'],'aeeed9bbccd4d02ee5c0109b86d86835f995330da4c265957d157751f604d404')

    def test_put_capability_signs_create_only_header_and_session_token(self):
        descriptor={'mediaType':'application/octet-stream','digest':'sha256:'+'b'*64,'size':10}
        now=dt.datetime(2026,9,10,16,0,tzinfo=dt.timezone.utc)
        with patch.object(M,'mint_temporary_credentials',return_value={'accessKeyId':'TMPKEY','secretAccessKey':'TMPSECRET','sessionToken':'TMPSESSION'}), patch.object(M,'parse_account_token',return_value={'account_id':'a'*32}):
            cap=M.issue_capability(operation='PUT',bucket='mailbox',descriptor=descriptor,ttl_seconds=300,now=now)
        q=dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(cap['url']).query))
        self.assertEqual(cap['requiredHeaders'],{'If-None-Match':'*'})
        self.assertIn('if-none-match',q['X-Amz-SignedHeaders'])
        self.assertEqual(q['X-Amz-Security-Token'],'TMPSESSION')
        self.assertNotIn('TMPSECRET',cap['url'])

    def test_durable_summary_never_persists_bearer_url_or_header_values(self):
        d={'mediaType':'application/octet-stream','digest':'sha256:'+'c'*64,'size':1}
        cap=M.capability_projection(operation='PUT',url='https://example.test/x?X-Amz-Signature=secret',descriptor=d,required_headers={'If-None-Match':'*'},expires_at='2026-09-10T16:05:00Z')
        summary=M.durable_capability_summary(cap)
        text=json.dumps(summary)
        self.assertNotIn('X-Amz-Signature',text);self.assertNotIn('secret',text);self.assertNotIn('https://',text);self.assertEqual(summary['requiredHeaderNames'],['If-None-Match'])

    def test_capability_expiry_and_replay_semantics_are_explicit(self):
        d={'mediaType':'application/octet-stream','digest':'sha256:'+'e'*64,'size':1}
        cap=M.capability_projection(operation='GET',url='https://example.test/x?sig=secret',descriptor=d,required_headers={},expires_at='2026-09-10T16:05:00Z')
        fresh=M.capability_standing(cap,now=dt.datetime(2026,9,10,16,4,59,tzinfo=dt.timezone.utc))
        expired=M.capability_standing(cap,now=dt.datetime(2026,9,10,16,5,0,tzinfo=dt.timezone.utc))
        self.assertEqual(fresh['standing'],'FRESH');self.assertTrue(fresh['usableNow']);self.assertIn('REPLAYABLE',fresh['replayStanding'])
        self.assertEqual(expired['standing'],'EXPIRED');self.assertFalse(expired['usableNow'])

    def test_unknown_put_response_never_becomes_effect_truth(self):
        data=b'payload';d=M.content_descriptor(data,'application/octet-stream')
        unknown=M.reconcile_put_effect(observed_existing=None,candidate=data,descriptor=d,observation_available=False)
        self.assertEqual(unknown['standing'],'UNKNOWN_PROVIDER_EFFECT');self.assertEqual(unknown['retryStanding'],'RECONCILE_BEFORE_RETRY');self.assertFalse(unknown['safeToOverwrite'])

    def test_put_reconciliation_distinguishes_absent_exact_and_conflicting_remote_state(self):
        data=b'payload';d=M.content_descriptor(data,'application/octet-stream')
        absent=M.reconcile_put_effect(observed_existing=None,candidate=data,descriptor=d,observation_available=True)
        exact=M.reconcile_put_effect(observed_existing=data,candidate=data,descriptor=d,observation_available=True)
        conflict=M.reconcile_put_effect(observed_existing=b'xxxxxxx',candidate=data,descriptor=d,observation_available=True)
        self.assertEqual(absent['standing'],'ABSENT_AFTER_OBSERVATION');self.assertEqual(absent['retryStanding'],'CREATE_ONCE_ALLOWED')
        self.assertEqual(exact['standing'],'COMMITTED_EXACT');self.assertEqual(exact['retryStanding'],'NO_WRITE_REQUIRED')
        self.assertEqual(conflict['standing'],'CONFLICTING_REMOTE_BYTES');self.assertEqual(conflict['retryStanding'],'HOLD')
        self.assertFalse(conflict['safeToOverwrite'])

    def test_get_reconciliation_rejects_partial_wrong_and_unavailable_provider(self):
        data=b'payload';d=M.content_descriptor(data,'application/octet-stream')
        self.assertEqual(M.reconcile_get_effect(data=data,descriptor=d,observation_available=True)['standing'],'EXACT_BYTES_OBSERVED')
        self.assertFalse(M.reconcile_get_effect(data=data[:-1],descriptor=d,observation_available=True)['admitToIngress'])
        self.assertEqual(M.reconcile_get_effect(data=None,descriptor=d,observation_available=True)['standing'],'REMOTE_OBJECT_ABSENT')
        self.assertEqual(M.reconcile_get_effect(data=None,descriptor=d,observation_available=False)['standing'],'UNKNOWN_PROVIDER_EFFECT')

    def test_concurrent_duplicate_producers_converge_on_one_exact_object(self):
        data=b'same';d=M.content_descriptor(data,'application/octet-stream')
        first=M.reconcile_put_effect(observed_existing=None,candidate=data,descriptor=d,observation_available=True)
        second=M.reconcile_put_effect(observed_existing=data,candidate=data,descriptor=d,observation_available=True)
        self.assertEqual(first['retryStanding'],'CREATE_ONCE_ALLOWED')
        self.assertEqual(second['standing'],'COMMITTED_EXACT')
        self.assertEqual(second['retryStanding'],'NO_WRITE_REQUIRED')

    def test_transfer_receipt_binds_content_and_never_contains_capability(self):
        data=b'x';d=M.content_descriptor(data,'application/octet-stream');key=M.object_key(d)
        receipt=M.transfer_receipt(descriptor=d,object_key_value=key,operation='PUT',standing='COMMITTED_EXACT')
        text=json.dumps(receipt)
        self.assertEqual(receipt['truthRole'],'transport-effect-observation-not-input-authority-or-artifact-acceptance')
        self.assertNotIn('https://',text);self.assertNotIn('X-Amz-',text);self.assertNotIn('secret',text)
        with self.assertRaisesRegex(ValueError,'object key'):M.transfer_receipt(descriptor=d,object_key_value='objects/sha256/'+'0'*64,operation='PUT',standing='COMMITTED_EXACT')

    def test_r2_url_validation_rejects_cross_account_cross_bucket_and_non_https(self):
        account='a'*32;bucket='mailbox';key='objects/sha256/'+'f'*64
        good=M.r2_object_url(account,bucket,key)
        self.assertEqual(M.validate_r2_object_url(good,account_id=account,bucket=bucket,key=key)['host'],account+'.r2.cloudflarestorage.com')
        with self.assertRaisesRegex(ValueError,'exact account'):M.validate_r2_object_url(good.replace(account,'b'*32,1),account_id=account,bucket=bucket,key=key)
        with self.assertRaisesRegex(ValueError,'bucket/object'):M.validate_r2_object_url(good.replace('/mailbox/','/other/'),account_id=account,bucket=bucket,key=key)
        with self.assertRaisesRegex(ValueError,'exact account'):M.validate_r2_object_url(good.replace('https://','http://'),account_id=account,bucket=bucket,key=key)

    def test_transfer_intent_reuses_content_descriptor_and_preserves_authority_separation(self):
        d=M.content_descriptor(b'hello','application/octet-stream')
        intent=M.transfer_intent(descriptor=d,target_authority='artifact-golden-r1',relative_object='pdu/test.bin')
        self.assertEqual(intent['content'],d);self.assertEqual(intent['transport']['objectKey'],M.object_key(d));self.assertEqual(intent['targetAuthority'],'artifact-golden-r1')
        self.assertNotIn('url',json.dumps(intent).lower())
        with self.assertRaisesRegex(ValueError,'safe relative path'):M.transfer_intent(descriptor=d,target_authority='artifact-golden-r1',relative_object='../escape')

    def test_route_schema_requires_transport_and_exact_content_identity(self):
        import jsonschema
        schema=json.loads((ROOT/'artifact-delivery/r2-mailbox-v1.schema.json').read_text())
        d=M.content_descriptor(b'hello','application/octet-stream');intent=M.transfer_intent(descriptor=d,target_authority='artifact-golden-r1',relative_object='pdu/test.bin')
        jsonschema.validate(intent,schema)
        broken=dict(intent);broken.pop('transport')
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(broken,schema)

    def test_operator_config_binds_existing_bucket_account_token_and_golden_authority_only(self):
        cfg=M.load_operator_config(ROOT/'config/artifact-r2-mailbox-r1.json')
        self.assertEqual(cfg['bucket'],'ordivon-artifacts');self.assertEqual(cfg['credentialRef'],'cloudflare-account-api-token');self.assertEqual(cfg['allowedTargetAuthorities'],['artifact-golden-r1']);self.assertEqual(cfg['createOnly'],{'header':'If-None-Match','value':'*'})

    def test_cli_has_no_bearer_capability_stdout_issue_surface(self):
        source=(ROOT/'scripts/artifact_r2_mailbox.py').read_text()
        main_source=source[source.index('def main() -> int:'):]
        self.assertNotIn("add_parser('issue')",main_source);self.assertIn("add_parser('inventory')",main_source)

    def test_account_token_parser_rejects_zero_trust_shape(self):
        with tempfile.TemporaryDirectory() as raw:
            p=Path(raw)/'cf.json';p.write_text(json.dumps({'token_type':'account','api_token':'x','account_id':'a'*32,'client_id':'zt'}))
            with self.assertRaisesRegex(RuntimeError,'Zero Trust'):M.parse_account_token(p)

    def test_r2_bucket_inventory_uses_account_token_verify_and_returns_only_resource_metadata(self):
        with tempfile.TemporaryDirectory() as raw:
            p=Path(raw)/'cf.json';p.write_text(json.dumps({'token_type':'account','api_token':'parent-secret','account_id':'a'*32,'api_base':'https://api.cloudflare.com/client/v4'}))
            calls=[]
            def fake(method,url,token,body=None):
                calls.append(url)
                if url.endswith('/accounts/'+'a'*32+'/tokens/verify'):
                    return 200,{'success':True,'result':{'status':'active','id':'parent-id'}}
                return 200,{'success':True,'result':{'buckets':[{'name':'z-bucket','jurisdiction':'default','location':'apac','storage_class':'Standard'},{'name':'a-bucket','jurisdiction':'default'}]}}
            with patch.object(M,'_provider_json',side_effect=fake):out=M.r2_bucket_inventory(p)
            self.assertEqual(out['accountTokenStanding'],'ACTIVE');self.assertEqual(out['r2ReadStanding'],'READ_AUTHORIZED');self.assertEqual([x['name'] for x in out['buckets']],['a-bucket','z-bucket']);self.assertNotIn('parent-secret',json.dumps(out));self.assertNotIn('/user/tokens/verify',' '.join(calls))

    def test_mint_temp_credentials_uses_api_token_verify_and_object_scope(self):
        with tempfile.TemporaryDirectory() as raw:
            p=Path(raw)/'cf.json';p.write_text(json.dumps({'token_type':'account','api_token':'parent-secret','account_id':'a'*32,'api_base':'https://api.cloudflare.com/client/v4'}))
            calls=[]
            def fake(method,url,token,body=None):
                calls.append((method,url,token,body))
                if url.endswith('/accounts/'+'a'*32+'/tokens/verify'):return 200,{'success':True,'result':{'status':'active','id':'parent-id'}}
                return 200,{'success':True,'result':{'accessKeyId':'tmp','secretAccessKey':'tmp-secret','sessionToken':'tmp-session'}}
            key='objects/sha256/'+'d'*64
            with patch.object(M,'_provider_json',side_effect=fake):creds=M.mint_temporary_credentials(bucket='mailbox',key=key,permission='object-read-only',ttl_seconds=300,credential_file=p)
            self.assertEqual(creds['accessKeyId'],'tmp');self.assertEqual(calls[0][0],'GET');self.assertTrue(calls[0][1].endswith('/accounts/'+'a'*32+'/tokens/verify'));self.assertEqual(calls[1][3]['objects'],[key]);self.assertEqual(calls[1][3]['parentAccessKeyId'],'parent-id')

if __name__=='__main__':unittest.main()
