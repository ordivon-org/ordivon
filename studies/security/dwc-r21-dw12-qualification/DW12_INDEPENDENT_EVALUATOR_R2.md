# DW12 Independent Evaluator Packet R2

This packet is for a genuinely independent evaluator occurrence. The candidate-building
occurrence must not create the final PASS receipt.

The evaluator must:

1. materialize the exact candidateRevision named by the packet;
2. verify packetDigest, subjectDigest, every allowed evidence file digest, evaluator
   implementation digest, runner digest, and the complete declared local evaluator dependency
   closure before evaluation;
3. use the frozen thresholds and missing-metric semantics exactly as written;
4. recompute the mechanical qualification without reading or adopting the candidate author's
   narrative conclusion as authority;
5. report any post-freeze mutation or threshold retuning as INVALID rather than silently
   accepting a new experiment;
6. preserve null production timing / human-attention metrics as UNKNOWN;
7. produce an independent evaluator receipt R2 with a distinct evaluatorActorRef and a concrete
   evaluatorOccurrenceRef.

A PASS receipt means the frozen mechanical claim was independently reproduced under the exact
packet. It does not establish production security outside the corpus, does not promote DW10 to
shared Composition, and does not close DW11's unexecuted human/Agent UX trials.
