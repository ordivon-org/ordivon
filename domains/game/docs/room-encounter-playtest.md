# Room Encounter — Human comprehension playtest (actual native build)

## Authority and research question

This is a human-observation protocol, not a game rule, AI grading rubric,
a simulated player, a new database or an online telemetry pipeline.

Question: Can a person operating the installed Godot Windows build
independently understand the *announced next hit*, stamina trade-off,
and timed charged-strike Guard? Does that comprehension lead to
deliberate choices? A successful Agent episode, formal proof, or
software screenshot cannot answer this question.

Methods: Godot official keyboard and controller focus guidance:
https://docs.godotengine.org/en/4.5/tutorials/ui/gui_navigation.html
Games User Research, The Think-Aloud Protocol (Oxford, 2018):
https://doi.org/10.1093/oso/9780198794844.003.0012
UCSC Game User Research methods:
https://gur.ucsc.edu/testing-methods
Game User Research playtest method choice:
https://gamesuserresearch.com/choose-the-right-playtest-method/
Avoid making causal claims from one exploratory think-aloud session;
speaking during play can change behavior. Use an uncoached first
run and optional retrospective questions rather than interrupting
every decision.

## Human procedure — no coaching during first encounter

Use the actual extracted Windows executable or a version-identical
Linux package. Verify its SHA-256 against the QA receipt. Start a
fresh Game run. Ask for consent to keep anonymous session notes
BEFORE recording anything. Declines get no notes or measures.
Follow balanced AB/BA assignments in the private study plan; never
change assignment retrospectively or instruct the participant
how to win. Classic has no charged-strike forecast, therefore its
forecast/parry entries are not_applicable rather than failed.
The Trial is selected with T or its button; C returns to Classic.
Observe whether the person finds controls from the onscreen labels.

The facilitator says only: "Play this game as you normally would.
You can talk about what you are trying to do. Please let me know if
any part of the interface is confusing. I will not explain the
strategy until the end." Do not tell the player exactly when to
Guard or which dialogue response to select.

Record in the blank CSV template only:
- platform/build digest and condition (Classic or Trial);
- elapsed session time, win/loss/quit, and observed stuck moments;
- whether the person discovers T/C, A/Space, G, N, and the gate choice;
- whether they can describe *which* next hit is predicted (not just read a number);
- any documented action choice and voluntarily offered explanation;
- observed focus/keyboard navigation trouble, clipping or hidden controls;
- participant's voluntary, brief post-session response to "What would you change?"

After first run, ask: "What does NEXT FOE HIT tell you?",
"When would Guard be better than Attack here?", and
"What happened to your health or stamina after a Guard?"
Do not imply correctness in the question. Preserve uncertainty: an
unanswered question is UNKNOWN, not FALSE.

No personal names, device serials, recordings, IP addresses or account
identifiers are necessary. Use a local arbitrary session code, not
a participant identifier. If someone voluntarily consents to a screen
recording, store that separately under their control; the template
does not require it.

## Decision and falsifiers

If the same point repeatedly confuses uncoached players, prefer first
to edit its visible explanation, focus, contrast, or timing rather than
creating a new combat framework. If the scene finishes much faster than
a meaningful 5-minute session, report the duration and do not
silently pad the game. If it takes much longer because the player
cannot find a control, that is friction, not content depth.

Mechanical hypothesis: a forecast-aware policy can complete the fixed
Trial retaining more HP than a naive attack-first policy; this was
measured with native rules in one bounded fixture (9 vs 6 HP) and is
not evidence of Human preferences or statistical significance.

Experimental evidence remains UNKNOWN until actual independent people
play and submit optional non-identifying observations. Do not mark the
product ready just because automated tests, four Viewport screenshots,
and a Windows native window-smoke pass.

## Agent operation — distinct from Human results

The already installed G11 entrypoint receives only visible UI/status/
hint/button-availability unless explicit debug mode is selected.
The bounded native episode proves deterministic state and dialogue
operation; its successful run must never be counted as a Human
playtest or five-minute Human session.

Canonical empty template: docs/room-encounter-playtest-template.csv. Game's res:// scene never imports research-only CSV.


## Offline anonymous study plan, validator and report

From domains/game/, supply the actual exported Windows/ Linux archive.
For a balanced four-pair design (8 planned sessions), use:

    python3 research/room_encounter_playtest.py prepare \
      --build dist/room-encounter/room-encounter-windows-x86_64.zip \
      --platform windows --pairs 4 \
      --out dist/room-encounter/private-study-01

The local command computes the archive SHA-256 and randomizes equal
numbers of Classic-then-Trial and Trial-then-Classic within-subject
pairs. It creates plan.csv and observations.csv with only blank
response fields. Those are NOT Human observations. It refuses to
overwrite a study directory. Keep this directory private; do not
commit raw responses or participant identifiers.

The facilitator follows the plan period order, asks consent, then
enters one row for each session using a plain CSV editor:
- consent_to_notes: yes/no; no => all response fields empty.
- session_seconds: elapsed time in seconds (1..21600), not an
  inferred enjoyment or engagement score.
- outcome: win/loss/quit/unknown; quitting is not a loss.
- controls_discovered: pipe-separated names A, G, N, R, T, C, S, L,
  unlock, or unknown if nothing was observed.
- forecast_interpretation: understood/misunderstood/unknown/
  not_applicable. Use not_applicable in Classic.
- parry_decision_observed, keyboard_focus_issue, and
  blocked_or_clipped_content: yes/no/unknown/not_applicable. Missing
  evidence is unknown, never automatically no.
- post_session_feedback and observer_uncertainty: optional short
  non-identifying notes (<=500 characters). Do not enter names,
  emails, device IDs, IPs or recordings, or a formula beginning with
  =, +, -, or @. Notes are not included in aggregate reports.
- session_code, condition, platform and build_sha256 are frozen
  assignment metadata, not editable outcomes.

Validate and describe after actual consenting Human sessions:

    python3 research/room_encounter_playtest.py report \
      --plan dist/room-encounter/private-study-01/plan.csv \
      --observations dist/room-encounter/private-study-01/observations.csv \
      --build dist/room-encounter/room-encounter-windows-x86_64.zip

The reader rejects malformed/unplanned/duplicated session codes,
wrong randomized condition or SHA-256, invalid categorical values,
unconsented data, and spreadsheet formula injection. It counts
planned, declined, pending, completed and missing evidence
separately. UNKNOWN is not NO. Aggregate condition summaries are
descriptive (with explicit denominators); no p-values, causal
claim, claim of game enjoyment or automatic product decision.

This is deliberately a small offline CSV layer, not a second
database, in-game tracking system, or fake Human evidence. It cannot
verify that an actual person played; human recruitment and authentic
observation are separate external conditions.

Execute the synthetic falsification controls before use:

    mise run test:human-playtest-protocol

A passing protocol test or empty study preparation always leaves
real Human comprehension and enjoyment at UNKNOWN.

On POSIX the generated private study directory and CSVs are created with mode 0700/0600. On Windows, verify the local NTFS ACL grants access only to the intended observer; chmod alone does not establish Windows ACL isolation.

The assignment CSV itself is an editable local file, not a signed research attestation. Validation checks internal shape, counterbalancing and consistency, but cannot authenticate the investigator or prevent coordinated modification of both plan and responses.
