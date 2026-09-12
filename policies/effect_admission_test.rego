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
  "actorId": "actor:red",
  "authorityId": "range-authority:red",
  "zoneRef": "zone:battlefield",
  "capability": "range-network",
  "effectType": "fabric.replace-peer",
}, overrides)

input_for(req) := {
  "actorIds": ["actor:red", "actor:blue"],
  "authorities": base_authorities,
  "request": req,
}

test_admitted if {
  decision.reason == "admitted" with input as input_for(request({}))
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
