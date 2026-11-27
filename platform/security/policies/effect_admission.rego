package ordivon.security.v2.effect_admission

import rego.v1

matching_authorities := [authority |
  authorities_contract_valid
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

nonempty_string(value) if {
  is_string(value)
  count(value) > 0
}

string_array(value) if {
  is_array(value)
  every item in value {
    nonempty_string(item)
  }
}

authority_contract_valid(authority) if {
  is_object(authority)
  allowed := {"authorityId", "actorId", "zoneRefs", "capabilities", "authorityDigest"}
  every key in object.keys(authority) { key in allowed }
  nonempty_string(authority.authorityId)
  nonempty_string(authority.actorId)
  string_array(authority.zoneRefs)
  string_array(authority.capabilities)
  nonempty_string(authority.authorityDigest)
}

authorities_contract_valid if {
  is_array(input.authorities)
  every authority in input.authorities {
    authority_contract_valid(authority)
  }
}

input_contract_valid if {
  is_object(input)
  allowed := {"schemaVersion", "actorIds", "authorities", "request"}
  every key in object.keys(input) { key in allowed }
  string_array(input.actorIds)
  authorities_contract_valid
  request_contract_valid
}

# A direct OPA consumer must not bypass the typed public adapter.
# The authorityDigest remains optional here so that the established
# "authority-digest-unbound" denial remains stable for missing/stale bindings.
request_contract_valid if {
  is_object(input.request)
  allowed := {"requestId", "requestDigest", "authorityDigest", "actorId", "authorityId", "zoneRef", "capability", "effectType"}
  every key in object.keys(input.request) { key in allowed }
  nonempty_string(input.request.requestId)
  valid_sha256(input.request.requestDigest)
  nonempty_string(input.request.actorId)
  nonempty_string(input.request.authorityId)
  nonempty_string(input.request.zoneRef)
  nonempty_string(input.request.capability)
  nonempty_string(input.request.effectType)
}

# Invalid inputs still produce a defined DENY projection, never an undefined
# decision or an ALLOW inferred from a separately evaluated reason.
safe_request_string(field) := value if {
  is_object(input)
  req := object.get(input, "request", null)
  is_object(req)
  value := object.get(req, field, null)
  is_string(value)
} else := null

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
else := "invalid-input" if {
  bound_contract
  not input_contract_valid
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
  "requestId": safe_request_string("requestId"),
  "requestDigest": safe_request_string("requestDigest"),
  "actorId": safe_request_string("actorId"),
  "authorityId": safe_request_string("authorityId"),
  "authorityDigest": authority_digest,
  "zoneRef": safe_request_string("zoneRef"),
  "capability": safe_request_string("capability"),
  "effectType": safe_request_string("effectType"),
  "admitted": reason == "admitted",
  "reason": reason,
  "inputContractVersion": 2,
  "authorityDigestBound": authority_digest_bound_value,
}
