package market_capital.external_write

default allow := false

allow if {
    input.state == "ADMITTED"
    input.externalFinancialWriteAllowed == true
    input.providerWriteCapabilityBound == true
    input.effectVerifier == "IMPLEMENTED_BOUND_CURRENT"
}
