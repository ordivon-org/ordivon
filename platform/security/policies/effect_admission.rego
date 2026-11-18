package ordivon.security.v2.effect_admission

import rego.v1

matching_authorities := [authority |
  some authority in input.authorities
  authority.authorityId == input.request.authorityId
]

authority_present if {
  count(matching_authorities) == 1
}

authority := matching_authorities[0] if authority_present

# Only the source-bound v2 contract is executable. Historical v1 comparison
# evidence remains available through Git history, not a downgradeable policy.
bound_contract if {
  input.schemaVersion == 2
}

valid_sha256(value) if {
  is_string(value)
  regex.match("^sha256:[0-9a-f]{64}$", value)
}

authority_digest_bound if {
  bound_contract
  authority_present
  valid_sha256(authority.authorityDigest)
  valid_sha256(input.request.authorityDigest)
  authority.authorityDigest == input.request.authorityDigest
}

authority_digest_bound_value := true if authority_digest_bound else := false

actor_known if {
  input.request.actorId in input.actorIds
}

zone_granted if {
  authority_present
  input.request.zoneRef in authority.zoneRefs
}

capability_granted if {
  authority_present
  input.request.capability in authority.capabilities
}

reason := "unsupported-contract-version" if {
  not bound_contract
}
else := "unknown-actor" if {
  bound_contract
  not actor_known
}
else := "unknown-authority" if {
  actor_known
  not authority_present
}
else := "authority-actor-mismatch" if {
  actor_known
  authority_present
  authority.actorId != input.request.actorId
}
else := "zone-not-granted" if {
  actor_known
  authority_present
  authority.actorId == input.request.actorId
  not zone_granted
}
else := "capability-not-granted" if {
  actor_known
  authority_present
  authority.actorId == input.request.actorId
  zone_granted
  not capability_granted
}
else := "authority-digest-unbound" if {
  bound_contract
  actor_known
  authority_present
  authority.actorId == input.request.actorId
  zone_granted
  capability_granted
  not authority_digest_bound
}
else := "admitted"

authority_digest := authority.authorityDigest if authority_present
else := null

decision := {
  "schemaVersion": 1,
  "kind": "ordivon.security.effect-admission",
  "requestId": input.request.requestId,
  "requestDigest": input.request.requestDigest,
  "actorId": input.request.actorId,
  "authorityId": input.request.authorityId,
  "authorityDigest": authority_digest,
  "zoneRef": input.request.zoneRef,
  "capability": input.request.capability,
  "effectType": input.request.effectType,
  "admitted": reason == "admitted",
  "reason": reason,
  "inputContractVersion": 2,
  "authorityDigestBound": authority_digest_bound_value,
}
