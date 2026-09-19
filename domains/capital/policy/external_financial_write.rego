package market_capital.execution

default allow_non_live := false
default allow_external_write := false

allow_non_live if {
    input.currentLane == "NON_LIVE"
    input.writePolicy.state == "NOT_ADMITTED"
    input.writePolicy.externalFinancialWriteAllowed == false
    input.writePolicy.providerWriteCapabilityBound == false
    input.writePolicy.effectVerifier != "IMPLEMENTED_BOUND_CURRENT"
}

allow_external_write if {
    input.currentLane == "EXTERNAL_WRITE"
    input.writePolicy.state == "ADMITTED"
    input.writePolicy.externalFinancialWriteAllowed == true
    input.writePolicy.providerWriteCapabilityBound == true
    input.writePolicy.effectVerifier == "IMPLEMENTED_BOUND_CURRENT"
}
