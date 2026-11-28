package ordivon.security.v2.effect_admission

import rego.v1

base_authorities := [
  {
    "authorityId": "range-authority:red",
    "actorId": "actor:red",
    "zoneRefs": ["zone:battlefield"],
    "capabilities": ["native-execution", "range-network"],
    "authorityDigest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  },
  {
    "authorityId": "range-authority:blue",
    "actorId": "actor:blue",
    "zoneRefs": ["zone:battlefield"],
    "capabilities": ["native-execution", "range-network"],
    "authorityDigest": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  },
]

request(overrides) := object.union({
  "requestId": "range-effect-request:test",
  "requestDigest": "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "authorityDigest": base_authorities[0].authorityDigest,
  "actorId": "actor:red",
  "authorityId": "range-authority:red",
  "zoneRef": "zone:battlefield",
  "capability": "range-network",
  "effectType": "fabric.replace-peer",
}, overrides)

input_for(req) := {
  "schemaVersion": 2,
  "actorIds": ["actor:red", "actor:blue"],
  "authorities": base_authorities,
  "request": req,
}

test_admitted if {
  decision.reason == "admitted" with input as input_for(request({}))
  decision.kind == "ordivon.security.effect-admission" with input as input_for(request({}))
  decision.admitted with input as input_for(request({}))
}

test_unknown_actor_precedes_other_checks if {
  decision.reason == "unknown-actor" with input as input_for(request({"actorId":"actor:ghost", "authorityId":"range-authority:fake"}))
}

test_unknown_authority if {
  decision.reason == "unknown-authority" with input as input_for(request({"authorityId":"range-authority:fake"}))
}

test_authority_actor_mismatch if {
  decision.reason == "authority-actor-mismatch" with input as input_for(request({"authorityId":"range-authority:blue"}))
}

test_zone_not_granted if {
  decision.reason == "zone-not-granted" with input as input_for(request({"zoneRef":"zone:elsewhere"}))
}

test_capability_not_granted if {
  decision.reason == "capability-not-granted" with input as input_for(request({"capability":"destroy-world"}))
}

# Bounded v2 source-readset binding. This is not a claim that caller-supplied
# authorities are themselves authentic: provenance must come from the Owner.
bound_input(req) := input_for(req)

test_bound_v2_requires_exact_authority_digest if {
  req := request({"authorityDigest": base_authorities[0].authorityDigest})
  result := decision with input as bound_input(req)
  result.admitted == true
  result.inputContractVersion == 2
  result.authorityDigestBound == true
  result.authorityDigest == req.authorityDigest
}

test_bound_v2_rejects_stale_authority_digest if {
  req := request({"authorityDigest": base_authorities[1].authorityDigest})
  result := decision with input as bound_input(req)
  result.admitted == false
  result.reason == "authority-digest-unbound"
  result.authorityDigestBound == false
}

test_bound_v2_rejects_absent_request_authority_digest if {
  req := object.remove(request({}), {"authorityDigest"})
  result := decision with input as bound_input(req)
  result.admitted == false
  result.reason == "authority-digest-unbound"
}

test_bound_v2_rejects_unqualified_authority_record_digest if {
  old := base_authorities[0]
  broken := object.union(old, {"authorityDigest": "sha256:incomplete"})
  req := request({"authorityDigest": "sha256:incomplete"})
  i := object.union(bound_input(req), {
    "authorities": [broken, base_authorities[1]],
  })
  result := decision with input as i
  result.admitted == false
  result.reason == "authority-digest-unbound"
}

test_bound_v2_does_not_override_capability_denial if {
  req := request({
    "authorityDigest": base_authorities[0].authorityDigest,
    "capability": "not-granted",
  })
  result := decision with input as bound_input(req)
  result.admitted == false
  result.reason == "capability-not-granted"
}

test_unknown_contract_version_fails_closed if {
  req := request({"authorityDigest": base_authorities[0].authorityDigest})
  i := object.union(bound_input(req), {"schemaVersion": 3})
  result := decision with input as i
  result.admitted == false
  result.reason == "unsupported-contract-version"
}

test_legacy_v1_contract_is_not_a_downgrade_path if {
  i := object.union(input_for(request({})), {"schemaVersion": 1})
  result := decision with input as i
  result.admitted == false
  result.reason == "unsupported-contract-version"
}

test_missing_contract_version_is_not_a_downgrade_path if {
  i := object.remove(input_for(request({})), {"schemaVersion"})
  result := decision with input as i
  result.admitted == false
  result.reason == "unsupported-contract-version"
}

# A direct OPA caller cannot interpret malformed identity and effect shape as ALLOW.
test_malformed_request_digest_is_a_defined_deny if {
  req := request({"requestDigest": "not-a-sha256"})
  result := decision with input as input_for(req)
  result.admitted == false
  result.reason == "invalid-input"
  result.requestDigest == "not-a-sha256"
}

test_non_string_effect_type_is_a_defined_deny if {
  req := request({"effectType": 7})
  result := decision with input as input_for(req)
  result.admitted == false
  result.reason == "invalid-input"
  result.effectType == null
}

test_missing_request_identity_is_a_defined_deny if {
  req := object.remove(request({}), {"requestId", "requestDigest"})
  result := decision with input as input_for(req)
  result.admitted == false
  result.reason == "invalid-input"
  result.requestId == null
  result.requestDigest == null
}

test_extra_request_fields_are_rejected if {
  req := object.union(request({}), {"shadowAuthority": "untrusted"})
  result := decision with input as input_for(req)
  result.admitted == false
  result.reason == "invalid-input"
}

test_direct_opa_collection_shapes_fail_closed if {
  base := input_for(request({}))
  authority_with_extra := object.union(base_authorities[0], {"shadowAuthority": "untrusted"})
  authority_with_object_zones := object.union(base_authorities[0], {"zoneRefs": {"zone:battlefield": true}})
  authority_with_object_capabilities := object.union(base_authorities[0], {"capabilities": {"range-network": true}})

  cases := [
    object.union(base, {"actorIds": {"actor:red": true}}),
    object.union(base, {"actorIds": ["actor:red", 7]}),
    object.union(base, {"authorities": {"red": base_authorities[0]}}),
    object.union(base, {"authorities": [base_authorities[0], 7]}),
    object.union(base, {"authorities": [authority_with_object_zones, base_authorities[1]]}),
    object.union(base, {"authorities": [authority_with_object_capabilities, base_authorities[1]]}),
    object.union(base, {"authorities": [authority_with_extra, base_authorities[1]]}),
    object.union(base, {"shadowRoot": "untrusted"}),
  ]

  every bad_input in cases {
    result := decision with input as bad_input
    result.admitted == false
    result.reason == "invalid-input"
  }
}
