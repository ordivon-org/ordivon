# Review Lifecycle Evidence Schema R2

R2 is additive. R1 remains a valid frozen interface for ARIES + DISAPERE.

PeerSum introduces two objects that must not be collapsed into existing concepts:

```text
DiscussionMessage --replies_to--> DiscussionMessage
       |                            |
       +---- source-set membership-+
                    |
                    v
                Synthesis
               (meta-review)
```

A `discussion_message` preserves source role and native rating/confidence metadata without classifying every message as a concern or response. A `synthesis` represents the supplied meta-review artifact. `member_of_synthesis_source_set` means only that the message belongs to the dataset-defined source discussion for that meta-review; it does **not** claim that the meta-review mentions, supports, endorses, or correctly summarizes that message.

`paper_acceptance_native` remains source metadata outside the shared lifecycle semantics. Numeric official-review rating spread may be used as a structural stratification variable, but is not semantic disagreement truth.

All adapters remain virtual. ARIES, DISAPERE, and PeerSum raw bytes retain separate physical ownership and license/provenance boundaries.
