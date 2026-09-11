# OpenTofu boundary

OpenTofu is selected for declarative external/cloud infrastructure state such as supported DNS, Cloudflare resources, storage, hosts, and IAM resources.

Do not migrate provider-specific imperative scripts blindly. For each resource family:

1. prove a maintained provider/resource exists;
2. import current production state where appropriate;
3. plan with no unintended changes;
4. cut over authority only after the consumer accepts the plan;
5. retire the old imperative path after dependency proof.

Runtime execution evidence and owner semantic truth are not Terraform/OpenTofu state.
