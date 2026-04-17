from pfios.domain.common.enums import ReviewVerdict

TERMINAL_VERDICTS = {
    ReviewVerdict.VALIDATED,
    ReviewVerdict.PARTIALLY_VALIDATED,
    ReviewVerdict.INVALIDATED,
    ReviewVerdict.INCONCLUSIVE,
}
