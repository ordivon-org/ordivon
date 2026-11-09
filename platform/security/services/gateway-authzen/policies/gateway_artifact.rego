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
