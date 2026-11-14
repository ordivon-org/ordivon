package ordivon.security.gateway_artifact

import rego.v1

# Scope: a Gateway-authenticated Principal reading its own, already-verified
# Runtime Artifact. The Gateway PEP binds the real Owner Job to the original
# principal-scoped requestId BEFORE any Artifact bytes can be forwarded.
# Policy cannot independently prove that Job authorization or Runtime bytes.
default allow := false

valid_issuer if {
  input.subject.type == "user"
  input.subject.id == "principal:local-service:harness"
  input.subject.properties.issuer == "ordivon-local-service"
}

valid_issuer if {
  input.subject.type == "user"
  regex.match("^principal:cf-access:[0-9a-f]{64}$", input.subject.id)
  input.subject.properties.issuer == data.ordivon.security.gateway_artifact_config.cf_issuer
}

valid_owner if {
  input.resource.properties.ownerId == "runtime.linux"
}

valid_owner if {
  input.resource.properties.ownerId == "runtime.windows"
}

valid_resource if {
  input.resource.type == "ordivon.runtime.artifact"
  input.resource.properties.identityContract == "ordivon.runtime-artifact-resource-key.v1"
  valid_owner
  is_string(input.resource.properties.jobId)
  regex.match("^job-[a-zA-Z0-9._-]+$", input.resource.properties.jobId)
  is_string(input.resource.properties.operationRef)
  input.resource.properties.operationRef == sprintf("ordivon-exec:v1:%s:%s", [input.resource.properties.ownerId, input.resource.properties.jobId])
  is_string(input.resource.properties.artifactId)
  count(input.resource.properties.artifactId) > 0
  input.resource.id == sprintf("runtime-artifact:v1:%s.%s", [
    trim(base64url.encode(input.resource.properties.operationRef), "="),
    trim(base64url.encode(input.resource.properties.artifactId), "="),
  ])
}

allow if {
  valid_issuer
  input.action.name == "artifact.runtime"
  input.action.properties.gatewayTool == "artifact.read"
  valid_resource
}

# Host policy: reuse the existing AuthZEN evaluation and OPA policy-data file.
# The JSON is supplied by the Security operator through the already
# LoadCredential-backed policy_data path, NEVER by the MCP caller or Gateway
# Tool arguments. No grants in the file => no Host ALLOW.
#
# This intentionally does not mint/attest an Agent identity. It permits a
# verified ingress Principal to act as the exact ActorRef only when a trusted
# operator-provisioned, still-valid delegation binds the tool and resource.
host_target_ok if {
  input.action.name == "host.legacy-write"
  p := input.resource.properties
  input.resource.type == "ordivon.host.legacy-write-request"
  p.identityContract == "ordivon.host-legacy-write-resource.v1"
  p.toolName == input.action.properties.gatewayTool
  is_string(p.claimedActorRef)
}

host_target_ok if {
  input.action.name == "host.work.engagement.advance"
  input.action.properties.gatewayTool == "work.engagement.advance"
  input.resource.type == "ordivon.host.work-engagement"
  input.resource.properties.identityContract == "ordivon.host-engagement-request-resource.v1"
  is_string(input.resource.properties.claimedActorRef)
  is_string(input.resource.properties.workRef)
  is_string(input.resource.properties.actionType)
}

host_target_ok if {
  input.action.name == "host.work.engagement.list"
  input.action.properties.gatewayTool == "work.engagement.list"
  input.resource.type == "ordivon.host.work-engagement-inbox"
  input.resource.properties.identityContract == "ordivon.host-engagement-request-resource.v1"
}

# R18: existing AuthZEN+OPA grants also mediate original Host reads.
# The Gateway derives these selectors from the *real* read Tool; the caller
# cannot use an ignored actorRef as an authentication or scope shortcut.
host_read_selector_fields := {
  "host.status": [],
  "work.get": ["workRef"],
  "work.list": [],
  "space.get": ["spaceRef"],
  "space.list": ["actorRef", "subjectRef"],
  "space.participation.list": ["spaceRef"],
  "space.subject.list": ["spaceRef"],
  "topic.cursor.get": ["actorRef", "topicRef"],
  "topic.list": ["spaceRef"],
  "topic.resume": ["topicRef"],
  "message.get": ["messageRef"],
  "message.search": ["spaceRef", "topicRef"],
  "message.relation.list": ["messageRef"],
  "subscription.list": ["actorRef"],
  "attention.get": ["actorRef"],
  "attention.delta": ["actorRef"],
  "attention.reentry": ["actorRef"],
}

host_read_required_fields := {
  "work.get": ["workRef"],
  "space.get": ["spaceRef"],
  "space.participation.list": ["spaceRef"],
  "space.subject.list": ["spaceRef"],
  "topic.cursor.get": ["actorRef", "topicRef"],
  "topic.list": ["spaceRef"],
  "topic.resume": ["topicRef"],
  "message.get": ["messageRef"],
  "message.relation.list": ["messageRef"],
  "subscription.list": ["actorRef"],
  "attention.get": ["actorRef"],
  "attention.delta": ["actorRef"],
  "attention.reentry": ["actorRef"],
}

host_target_ok if {
  input.action.name == "host.legacy-read"
  p := input.resource.properties
  input.resource.type == "ordivon.host.legacy-read-request"
  p.identityContract == "ordivon.host-legacy-read-resource.v1"
  p.toolName == input.action.properties.gatewayTool
  is_string(p.requestSha256)
  regex.match("^[0-9a-f]{64}$", p.requestSha256)
  is_object(p.requestedSelectors)
  is_boolean(p.unscoped)
  p.unscoped == (count(p.requestedSelectors) == 0)
  allowed := host_read_selector_fields[p.toolName]
  every field, value in p.requestedSelectors {
    field in allowed
    is_string(value)
    count(value) > 2
  }
  required := object.get(host_read_required_fields, p.toolName, [])
  every field in required {
    is_string(p.requestedSelectors[field])
  }
  input.resource.id == sprintf("host-legacy-read:v1:%s.%s", [
    trim(base64url.encode(p.toolName), "="), p.requestSha256
  ])
}

# The field used for authorization is determined by the *actual Owner tool*,
# never by a second caller-supplied actorRef/resourceRef that the Owner ignores.
host_scope(tool, props) := ref if {
  tool in {"work.create", "work.snapshot.commit", "work.engagement.advance"}
  ref := props.workRef
}
host_scope(tool, props) := ref if {
  tool in {"space.create", "space.participation.set"}
  ref := props.spaceRef
}
host_scope(tool, props) := ref if {
  tool in {"topic.create", "topic.cursor.ack", "topic.state.set", "message.post"}
  ref := props.topicRef
}
host_scope(tool, props) := ref if {
  tool in {"subscription.follow", "subscription.unfollow"}
  ref := props.targetRef
}
host_scope(tool, props) := ref if {
  tool in {"actor.declare", "attention.ack"}
  ref := props.claimedActorRef
}
host_scope(tool, props) := ref if {
  tool == "message.relation.add"
  ref := props.sourceMessageRef
}

host_scope_granted(grant, ref) if {
  is_string(ref)
  count(ref) > 0
  some exact_ref in grant.exactRefs
  is_string(exact_ref)
  exact_ref == ref
}
host_scope_granted(grant, ref) if {
  is_string(ref)
  some prefix in grant.namespacePrefixes
  is_string(prefix)
  count(prefix) >= 6
  endswith(prefix, ":")
  startswith(ref, prefix)
}

# A filtered inbox may only return Works for the explicitly delegated Actor,
# never the unfiltered global inbox or another Actor's inbox.
host_inbox_granted(grant) if {
  p := input.resource.properties
  host_actor_matches(grant, p.requestedAssigneeActorRef)
  p.requestedConsumerActorRef == null
}
host_inbox_granted(grant) if {
  p := input.resource.properties
  host_actor_matches(grant, p.requestedConsumerActorRef)
  p.requestedAssigneeActorRef == null
}
host_inbox_granted(grant) if {
  p := input.resource.properties
  host_actor_matches(grant, p.requestedConsumerActorRef)
  host_actor_matches(grant, p.requestedAssigneeActorRef)
}

# A named Agent grant remains exact by default. A separately provisioned
# operator role may delegate bounded Actor namespace prefixes to one verified
# Principal. These prefixes exist ONLY in trusted Security policy data; MCP
# payload fields and opaque Actor declarations cannot create a grant.
host_actor_matches(grant, actor_ref) if {
  is_string(actor_ref)
  actor_ref == grant.actorRef
}
host_actor_matches(grant, actor_ref) if {
  grant.role == "operator"
  is_array(grant.delegatedActorPrefixes)
  is_string(actor_ref)
  some prefix in grant.delegatedActorPrefixes
  is_string(prefix)
  count(prefix) >= 6
  endswith(prefix, ":")
  startswith(actor_ref, prefix)
  count(actor_ref) > count(prefix)
}

# Resource-scoped reads are qualified against the same trusted operator
# Actor Grant as writes. Every provided selector must be admitted. A Principal
# may inspect the whole Host inventory only when the operator explicitly
# provisions allowUnscopedReads for the specific Tool.
host_read_selector_granted(grant, field, value) if {
  field == "actorRef"
  host_actor_matches(grant, value)
}
host_read_selector_granted(grant, field, value) if {
  field in {"workRef", "spaceRef", "topicRef", "messageRef", "subjectRef"}
  host_scope_granted(grant, value)
}

host_read_scope_granted(grant) if {
  input.resource.properties.unscoped == true
  grant.allowUnscopedReads == true
}
host_read_scope_granted(grant) if {
  p := input.resource.properties
  p.unscoped == false
  count(p.requestedSelectors) > 0
  every field, value in p.requestedSelectors {
    host_read_selector_granted(grant, field, value)
  }
}

host_actor_granted(grant) if {
  input.action.name == "host.legacy-read"
  host_read_scope_granted(grant)
}

host_actor_granted(grant) if {
  input.action.name == "host.work.engagement.list"
  host_inbox_granted(grant)
}
host_actor_granted(grant) if {
  input.action.name != "host.work.engagement.list"
  host_actor_matches(grant, input.resource.properties.claimedActorRef)
  tool := input.action.properties.gatewayTool
  scope_ref := host_scope(tool, input.resource.properties)
  host_scope_granted(grant, scope_ref)
  # A relationship cannot link a delegated source into an unrelated object
  # unless the target is also within the operator-approved resource scope.
  host_relation_target_granted(grant, tool)
}

host_relation_target_granted(_, tool) if {
  tool != "message.relation.add"
}
host_relation_target_granted(grant, tool) if {
  tool == "message.relation.add"
  host_scope_granted(grant, input.resource.properties.targetRef)
}

host_action_granted(_) if {
  input.action.name != "host.work.engagement.advance"
}
host_action_granted(grant) if {
  input.action.name == "host.work.engagement.advance"
  action_type := input.resource.properties.actionType
  action_type in grant.allowedActions
}

valid_host_delegation if {
  valid_issuer
  host_target_ok
  some grant in data.ordivon.security.gateway_host_actor_grants
  grant.active == true
  grant.principalId == input.subject.id
  grant.issuer == input.subject.properties.issuer
  is_string(grant.actorRef)
  grant.actorRef != ""
  is_number(grant.notBeforeEpochSeconds)
  is_number(grant.expiresAtEpochSeconds)
  now := time.now_ns() / 1000000000
  grant.notBeforeEpochSeconds <= now
  now < grant.expiresAtEpochSeconds
  is_array(grant.allowedTools)
  input.action.properties.gatewayTool in grant.allowedTools
  host_actor_granted(grant)
  host_action_granted(grant)
}

allow if {
  valid_host_delegation
}
