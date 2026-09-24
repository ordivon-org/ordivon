# PeerSum Meta-review Structure Baseline R1

Date: 2026-09-23
Source asset: `peersum-hf-bounded-core-r1`
Scope: **current exact PeerSum Hugging Face carrier only**

## Exact carrier

The bound carrier contains **14,993 papers** and **178,272 review/discussion messages**, including **79,354 official-review messages**, **95,943 author messages**, and **2,975 public messages**. All **14,993** papers contain a non-empty meta-review. The reply graph passed zero-orphan, zero-self-loop, and zero-cycle checks.

The exact current carrier split is **11,992 train / 1,496 val / 1,505 test**. Historical paper/README documentation reports **11,995 / 1,499 / 1,499**. R1 treats this as documented release drift and binds analyses to the current exact bytes rather than rewriting the carrier to the historical counts.

## Structural disagreement proxy

For each paper, R1 defines a deliberately coarse proxy: `max(official-review rating) - min(official-review rating)`. The median spread is **2**, mean **2.141**. **5,320 (35.48%)** papers have spread >=3; **2,032 (13.55%)** have spread >=4; **1,175 (7.84%)** have spread >=5.

This is **not semantic disagreement**. It is a numeric-rating dispersion descriptor used to stratify later analysis without pretending to identify contradictions in review text.

## Conversation and synthesis structure

A paper has median **11 messages** (IQR 8–15) and median **4 official-review messages**. Meta-reviews have median **105 whitespace-token words** (IQR 65–164).

## Ordivon implication

PeerSum adds a new relation that ARIES and DISAPERE did not provide:

`Discussion topology -> Synthesis artifact`

It should not be squeezed into `Response`. R2 therefore needs an explicit `discussion_message` / `synthesis` layer while preserving source-native roles, reply topology, rights, and decision boundaries.

## Interpretation ceiling

Rating spread is not semantic contradiction; meta-review is not scientific truth; acceptance metadata is not a universal quality label; and the observed frequencies are PeerSum-corpus properties rather than peer-review population estimates.
