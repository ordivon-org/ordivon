# ARIES Response→Revision Candidate Space R1

Status: **PASS_BOUNDED_SEMANTIC_CONTENT_AND_CANDIDATE_SPACE**
Relation standing: **NO_GOLD_RESPONSE_EDIT_RELATION_IN_SOURCE_ASSETS**

A bounded S2ORC semantic-content carrier now covers **36 documents / 72 source+target PDF identities**, producing **8,518 paragraphs** and **4,718 text-bearing edit units**. All selected edit paragraph indices resolve with zero missing PDF pairs and zero out-of-bounds source/target indices.

For the **87** manual concerns that already have both review-response context and positive revision correspondence, the current data induce **248 response×positive-edit candidates** across **36 documents**. Candidate count per concern has median **2**, IQR **1.0–4.0**, maximum **12**. Only **34** concerns are 1×1; **53** remain multi-candidate.

The candidate space contains **49 unique author responses**; **31** are reused across more than one concern, up to **5 concerns per response**. Therefore even a 1×1 local candidate must not be interpreted as response→edit gold: the response context is review-level rather than concern-specific.

The allowed next step is **independent/blinded semantic annotation** over this bounded candidate substrate. Model training, ranking evaluation, response adequacy claims, and causal interpretation remain blocked until a separately validated response-to-edit relation exists.

Rights remain fail-closed: the ARIES dataset license is observed, but underlying paper-text rights are not independently verified; external redistribution and commercial paper-text reuse are not authorized by the catalog.
