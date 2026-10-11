# Source-only policy gate; this is an Ordivon identity/authority invariant, not a VPN controller.
. as $r
| ($r.realizations | map(.realizationId)) as $ids
| ($r.realizations | map(select(.standing == "active"))) as $active
| ($r.realizations | map(select(.standing == "candidate"))) as $candidates
| (
    ($r.kind == "ordivon.network-v2.provider-carrier-realizations")
    and ($r.activeRealizationId == "legacy-wireguard-r1")
    and ($r.candidateRealizationIds == ["gluetun-v3.41.3-r1"])
    and (($ids | unique | length) == ($ids | length))
    and (($active | length) == 1)
    and (($candidates | length) == ($r.candidateRealizationIds | length))
    and (($active | map(.realizationId)) == [$r.activeRealizationId])
    and (($candidates | map(.realizationId) | sort) == ($r.candidateRealizationIds | sort))
    and (($active | length) + ($candidates | length) == ($r.realizations | length))
    and ($r.realizations | all(.[]
        ; .providerProfileRef == $r.providerProfileRef
        and .clientIdentityRef == $r.clientIdentityRef
        and .concurrentWithActive == false
    ))
    and ($active | all(.[]
        ; .productionAuthority == true
        and .activationMode == "continuous"
        and .artifactRef == null
    ))
    and ($candidates | all(.[]
        ; .productionAuthority == false
        and .activationMode == "serialized-only"
        and .artifactRef == {"kind":"oci-image","lockFile":"capabilities/gluetun/external/gluetun-image.lock"}
    ))
)
