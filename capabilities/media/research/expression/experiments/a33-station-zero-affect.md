# A3-3 — Station Zero affect / the map ends here

## Question

Can the Art & Expression Laboratory guide a **felt state** — isolation, latent dread, and fragile hope — without relying on an explanatory flowchart, hidden-world reveal, or invented narrative facts?

A3-1 tested clarity and persistence. A3-2 tested lawful ambiguity and revelation. A3-3 removes most explicit causal branching and asks whether composition, scale, rhythm, withholding, and focalization can shape affect while remaining source-bound.

## Frozen evidence

The experiment is bound to `a33-station-zero-affect-evidence.json`, derived from the executable **unregistered Station Zero v3 replacement-target** fixed Genesis. It must not be narrated as the registered v2 product.

At Turn 0, Rescue confirms only:

```text
Engineer Imani     rescue-airlock
Medic Reyes        rescue-airlock
Security Chen      command-deck

known rooms        Command Center / Power Junction / Medical Bay
known system       Power Grid · 72% · powered
known hazards      none
reports            distress-signal / unknown-life-signs
```

Public environment telemetry is:

```text
battery 48 / 48
oxygen 68
reactor heat 62
alert 2
```

The authoritative World contains more actors, systems, hazards, and rooms, but Rescue does not know their exact hidden state at Genesis. A3-3 must not reveal those details merely to create fear.

## Affect target

Primary:

- **isolation** — three confirmed people occupy a very small island of certainty;
- **latent dread** — the station is not empty, but the threat is unresolved rather than shown;
- **fragility** — life-supporting conditions are already bounded and coupled;
- **fragile hope** — the team is healthy, capable, and together; mandatory Rescue objectives provide direction while `report:distress-signal` remains part of the admitted report set.

Secondary: presence, transportation, interest, memorability.

The target is **not** panic, gore, jump scare, or “everything is doomed.”

## Expression priors used

From the existing laboratory evidence map:

- narrative is information under a perspective;
- transportation depends on sustained attention, imagery, affect, and coherent perspective;
- prediction/surprise requires a pattern before a departure has force;
- fluency is useful for entry but does not maximize interest or profundity;
- context changes aesthetic and emotional interpretation;
- color/scale/contrast are systems, not universal emotion dictionaries.

## Tension profile

| Tension | Chosen region | Reason |
| --- | --- | --- |
| unity ↔ variety | severe unity, tiny local variation | the environment should feel larger than the known team |
| fluency ↔ challenge | immediate local certainty, unresolved global model | the viewer understands what is known but cannot close the world model |
| familiarity ↔ novelty | familiar station telemetry, unusual amount of empty/unknown field | dread comes from missing structure rather than exotic widgets |
| predictability ↔ surprise | slow repeated signal rhythm, no jump event | threat should remain latent rather than discharge into spectacle |
| continuity ↔ discontinuity | continuous station ambience, broken knowledge continuity | the map literally stops before the world does |
| restraint ↔ expression | strong restraint; one distant signal and one human cluster | scale and absence carry the affect |
| explicitness ↔ ambiguity | local facts explicit, remote meaning ambiguous | unknown-life-signs must stay unknown |
| density ↔ breathing room | extreme breathing room | unused field represents unobserved station, not decorative luxury |

## Focalization

A3-3 stays close to the **Rescue player/commander knowledge envelope** in both media. Unlike A3-2 Motion, the audience does not receive privileged hidden-world positions.

This is deliberate: the affect should come from **epistemic absence**, not from dramatic irony.

## Web hypothesis — the map ends here

Web should use spatial scale and scroll pause:

- a small cluster of three confirmed Rescue contacts;
- three known rooms rendered as a compact island;
- the remainder of the composition left structurally unresolved rather than populated with fake enemy silhouettes;
- global telemetry presented quietly at the perimeter;
- `report:unknown-life-signs` appears as a distant report, not a located enemy marker;
- the section should contain substantially more negative space than the surrounding project page;
- the next normal engineering section should feel like re-entry into analysis after a brief experiential pause.

The key sentence is not “enemies are nearby.” It is:

> **Your map ends before the station does.**

## Motion hypothesis — a signal in a dark station

Motion should use time without inventing state changes:

1. begin in near-darkness with a very small Rescue contact cluster;
2. establish a slow, repeatable telemetry rhythm;
3. reveal only the three discovered rooms around the team;
4. let the known map stop while the frame remains mostly empty;
5. introduce the `unknown-life-signs` report as a distant non-localized pulse — never as a position;
6. preserve the team cluster and mandatory Rescue objectives as the source of fragile hope;
7. end without revealing the hidden threat.

No oxygen countdown, moving enemy contact, flickering reactor failure, death, or other temporal consequence may be fabricated. The World is frozen at Genesis.

## Anti-fabrication invariants

Do not visually invent:

- Pirate or Swarm positions in Rescue view;
- a direction for `unknown-life-signs`;
- hidden hazard identity or location;
- an oxygen trend from the single value `68`;
- a reactor-heat trend from the single value `62`;
- a communications/cooling/life-support state Rescue does not yet know;
- probability of attack;
- sounds, dialogue, casualties, or alarms not present in the source.

Affect must be produced from **scale, rhythm, withholding, framing, typography, and known facts**.

## Falsifiers

Revise or reject if:

- the work is merely a dark theme applied to a technical dashboard;
- viewers are shown hidden information to make the scene exciting;
- empty space reads as unfinished layout rather than bounded unknown;
- the three specialists disappear into atmosphere instead of remaining the emotional anchor;
- `unknown-life-signs` becomes a monster marker;
- the design implies oxygen or reactor values are worsening over time;
- the work produces only dread and erases the rescue objective / capable team;
- Web and Motion converge on the same diagram instead of exploiting spatial pause versus temporal rhythm.

## Evidence boundary

A3-3 can establish whether the laboratory produces a coherent, source-disciplined affect strategy and whether the rendered artifact implements that strategy. It cannot, without human/expert response evidence, claim that a population actually felt isolation, dread, or hope.


## First composition correction — unlocalized information needs unlocalized composition

The first Motion/Web layouts placed `unknown-life-signs` on the right side of the visual field. Even without an explicit connector, spatial placement can be read as a bearing. Because Rescue has no position for that report, the composition was revised to a wide HUD/report band that does not belong to the station-map coordinate field.

> Non-localized information can be accidentally localized by composition alone.


## First rendered result

A3-3 produced real Web and Motion artifacts from the frozen Genesis without introducing hidden enemy positions or fabricated time-series state.

### Web manipulation evidence

At 1440px, the known Rescue island occupies about `22.8%` of the affect field area. At 390px, it remains about `29.2%`; both layouts have no horizontal overflow. The final unlocalized report band spans about `62.5%` of the desktop field width and `91.3%` on mobile, preventing it from behaving like a map-localized contact.

```text
Web desktop  sha256:6a1c66f6911f55f1c9ed89a00c53cfe8bd7bae5651753c7b6d2aa0242c7634e9
Web mobile   sha256:33370cea627a9c235a99b22bb88a28830b910a925f8721022096b1bf33e5da35
Web baseline sha256:bf4be264b816cc6fb25599e692c4806e5b523e6f727a10195b159dab85504758
```

These ratios are diagnostics for the intended scale manipulation, not aesthetic scores.

### Motion render evidence

Five 1920×1080 checkpoints were rendered from `a33-station-zero-affect`:

```text
frame 24   local anchor / near-dark
           sha256:6a01c6bbadcd2e41c50f2aab12006da1fc62030032584ccb9cb417de34b29eb4
frame 84   known island forms
           sha256:47fcdfbad697f0eab7c641c310f5332d11c0aa862158c40d13a6f68897a6ddb3
frame 132  unlocalized report
           sha256:3ec8f2bb3b4770d159b8994b9f64a9e1d22f663bc299e4e02cdee539dbab87c7
frame 198  Rescue purpose remains
           sha256:a8d90e2b8bba443b51793053331f64c63156edbbce0caa24c0112c426e86e5e2
frame 252  no hidden-threat reveal
           sha256:51c38cb49b91bb4020810c45b06e32f86523e2381d613374d7713151f7971dbc
```

The composition changes visibility and emphasis over time, but no telemetry value changes and no hidden World actor/hazard is revealed.

## What A3-3 adds to the laboratory

A3-3 does not prove that an audience felt dread, isolation, or hope. It does establish that the laboratory can generate a materially different production strategy when the target is affect rather than explanation.

The strongest local findings are:

1. **negative space needs semantic authority** — empty-looking area only carries meaning when the work establishes that it represents unobserved space rather than absent content;
2. **spatial placement is itself a claim** — placing an unlocalized report on one side can invent a bearing even without an arrow or coordinate;
3. **affect can be source-disciplined** — tension can come from scale, withholding, rhythm, and focalization without inventing threat events;
4. **hope can be structural rather than tonal** — confirmed healthy specialists and mandatory Rescue objectives counterbalance dread without a motivational slogan or bright stylistic switch;
5. **medium transfer again occurs above geometry** — Web uses spatial pause and proportion; Motion uses temporal reveal and sustained unresolved framing.

A provisional cross-medium production rule is:

> **Absence becomes expressive only when the audience can distinguish “not present” from “not known.”**

That distinction is especially important for Agent-native worlds, where epistemic boundaries are part of the authored experience rather than merely hidden implementation state.

## Next pressure

A3-1 through A3-3 now cover clarity, lawful ambiguity, and bounded affect. The next useful step should stop adding one-off showcase sections and consolidate the surviving results into a compact reusable **Expression Decision Protocol** for Web/Studio Agents: experiential target → focalization/authority → tension profile → medium translation → render audit → claim boundary. Then test that protocol on an unrelated real production rather than continuing the numbered experiment loop indefinitely.
