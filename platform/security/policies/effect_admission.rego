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

reason := "unknown-actor" if {
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
else := "admitted"

authority_digest := authority.authorityDigest if authority_present
else := null

decision := {
  "schemaVersion": 1,
  "kind": "ordivon.security.range-effect-admission",
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
}
