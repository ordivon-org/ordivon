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
Avoid making causal claims from one exploratory think-aloud session;
speaking during play can change behavior.

## Human procedure — no coaching during first encounter

Use the actual extracted Windows executable or a version-identical
Linux package. Verify its SHA-256 against the QA receipt. Start a
fresh Game run. Let the participant choose Classic or Tactical Trial,
or use counterbalanced AB/BA order across participants. The Trial is
selected with T or its button; C returns to Classic. Observe whether
the person can find the controls using the onscreen labels.

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
