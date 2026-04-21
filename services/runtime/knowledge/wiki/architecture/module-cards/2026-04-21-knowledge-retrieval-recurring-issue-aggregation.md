# Module Card

- Module: Knowledge | Retrieval / Recurring Issue Aggregation
- Layer: Knowledge
- Role: Turn persisted lessons, extracted knowledge entries, and persisted feedback packets into a minimal retrieval layer plus a minimal recurring-issue aggregation layer, without promoting derived knowledge into policy truth.
- Current Value:
  - `LessonExtractionService` can derive `KnowledgeEntry` objects from persisted lesson and outcome facts.
  - `KnowledgeFeedbackPacket` is now a persisted object and can be read by governance and intelligence.
  - Knowledge feedback is already consumed downstream, but there is still no general retrieval entrypoint or recurring-pattern view.
- Remaining Gap:
  - There is no service that retrieves relevant knowledge by recommendation, review, or symbol.
  - There is no recurring-issue aggregation, so repeated lesson themes remain scattered across rows and packets.
  - Knowledge remains usable only through a few bespoke downstream readers.
- Immediate Action:
  1. Add a minimal `KnowledgeRetrievalService`.
  2. Support retrieval by:
     - recommendation id
     - review id
     - symbol
  3. Add a minimal recurring-issue aggregation result:
     - normalized issue key
     - occurrence count
     - sample lesson summaries
     - linked recommendation/review ids
  4. Keep all output derived from persisted lesson/outcome/feedback objects only.
- Required Test Pack:
  - `python -m compileall ...`
  - unit:
    - retrieval by recommendation/review/symbol
    - recurring issue aggregation normalization and counting
    - empty retrieval returns empty results honestly
  - integration:
    - completed reviews create retrievable knowledge
    - repeated lessons aggregate into recurring issue summaries
  - failure-path:
    - no lessons / no packets returns empty results
    - missing recommendation/review/symbol does not fabricate knowledge
  - invariants:
    - retrieval does not overwrite state truth
    - recurring issue output is candidate/derived, not policy update
    - evidence-backed knowledge only
  - state/data:
    - retrieved knowledge and recurring issues are traceable back to persisted lesson/outcome/packet objects
- Done Criteria:
  - There is a real retrieval service for persisted knowledge.
  - There is a real recurring-issue aggregation output.
  - Both outputs remain explicitly derived and evidence-backed.
  - Tests prove retrieval and aggregation work without fabricating truth.
- Next Unlock:
  - `Infrastructure | Health / Monitoring`
  - later rule candidate extraction
  - later knowledge surface/query API
- Not Doing:
  - Do not create policy rules automatically.
  - Do not add UI surface.
  - Do not create long-term memory or shared memory.
  - Do not turn recurring issues into governance truth.
