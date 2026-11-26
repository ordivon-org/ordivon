# Host release qualification

从 [Host Owner Guide](HOST_OWNER_GUIDE.md) 迁移的原契约。该文件承载相关职责的操作约束与历史资格证据；不另立运行时权威。

<a name="contract-1"></a>

## Host release SourceCut content-anchor refinement

The native packaging entrypoint accepts an optional fourth argument:
install_release.sh <repo> <main_commit> <prefix> <reviewed_host_tree_oid>.

Human: obtain expected Host Git tree ID from the independently reviewed PR
head via git rev-parse <head>:services/host; cross-check the actual merge
event against fetched main ancestry and commit subject. Pass the reviewed
tree ID as argument four. A wrong adjacent Merge Queue SHA with a different
Host tree fails before directory creation, dependency resolution or symlink
mutation. The three-argument native installation path stays compatible.

Agent: never compute the expected tree from the *same untrusted release
commit*: that would prove an identity against itself. Git native tree objects
obviate a second hash or independent custom release registry. This is a
content identity witness, not a signed SLSA provenance attestation or proof
of builder identity. Continue Git chronology, Merge Queue checks, immutable
archive verification and live MCP consumer readback. UNKNOWN remains UNKNOWN.
