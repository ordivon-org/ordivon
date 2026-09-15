#let paper = rgb("#f4efe6")
#let ink = rgb("#151515")
#let acid = rgb("#d8ff3e")
#let ember = rgb("#ff5a36")
#let mist = rgb("#dce8ff")
#let graphite = rgb("#343434")

#set page(width: 148mm, height: 210mm, margin: (x: 14mm, y: 14mm), fill: paper)
#set text(font: "Arial", fill: ink, size: 10pt)
#set par(leading: 1.15em, justify: false)

#let rule() = line(length: 100%, stroke: 0.8pt + ink)
#let label(x) = text(size: 7pt, weight: "bold", tracking: 0.12em)[#x]
#let big(x, s: 38pt) = text(size: s, weight: "black", tracking: -0.04em)[#x]
#let step(n, title, body) = block(width: 100%, inset: (top: 5pt, bottom: 8pt), stroke: (top: 0.7pt + ink))[
  #grid(columns: (18mm, 1fr), gutter: 4mm,
    [#text(size: 24pt, weight: "black")[#n]],
    [#text(size: 11pt, weight: "bold")[#title]\
     #text(size: 8.5pt, fill: graphite)[#body]]
  )
]

// 01 — COVER
#align(top + left)[
  #label("ORDIVON / FIELD NOTE 001")
  #v(22mm)
  #big("MAKE")
  #linebreak()
  #big("THINGS")
  #v(5mm)
  #box(fill: acid, inset: (x: 5pt, y: 3pt))[#text(size: 11pt, weight: "bold")[\+ FIND FRICTION]]
  #v(24mm)
  #rule()
  #v(4mm)
  #text(size: 8pt)[A small publication about creative work as a reality test.]
]
#place(bottom + right)[#text(size: 7pt, fill: graphite)[2026 · ORDIVON CREATIVE WORKS]]

#pagebreak()

// 02 — THESIS
#label("01 / THE LOOP")
#v(13mm)
#big("A WORK IS")
#linebreak()
#big("NOT AN IDEA.", s: 34pt)
#v(8mm)
#text(size: 15pt)[
It becomes useful when it survives contact with a tool, a file, a renderer, a player, a browser, a human, or another agent.
]
#v(12mm)
#box(width: 100%, fill: ink, inset: 8pt)[
  #set text(fill: paper)
  #text(size: 12pt, weight: "bold")[SELECT → CREATE → BUILD → CONSUME → INSPECT → REVISE → REGISTER]
]
#v(11mm)
#text(size: 8.5pt, fill: graphite)[The catalogue matters because work should remain findable. Consumption matters because existence is weaker than use.]

#pagebreak()

// 03 — TWO CONSEQUENCES
#label("02 / TWO CONSEQUENCES")
#v(13mm)
#grid(columns: (1fr, 1fr), gutter: 7mm,
  box(fill: acid, inset: 7pt, height: 95mm)[
    #text(size: 42pt, weight: "black")[A]
    #v(7mm)
    #text(size: 17pt, weight: "bold")[WORK]
    #v(3mm)
    #text(size: 9pt)[A new thing that can be opened, played, rendered, edited, inspected, cited, or reused.]
  ],
  box(fill: mist, inset: 7pt, height: 95mm)[
    #text(size: 42pt, weight: "black")[B]
    #v(7mm)
    #text(size: 17pt, weight: "bold")[IMPROVEMENT]
    #v(3mm)
    #text(size: 9pt)[A real obstruction discovered through use, then fixed, verified, or handed to the right owner.]
  ]
)
#v(12mm)
#text(size: 14pt, weight: "bold")[A strong round leaves one. A better round leaves both.]

#pagebreak()

// 04 — THE PRACTICE
#label("03 / THE PRACTICE")
#v(8mm)
#step("01", "MAKE", "Use an existing mature tool. Produce an editable source and a real deliverable.")
#step("02", "OPEN", "Render, play, run, or inspect the result with a real consumer instead of trusting file existence.")
#step("03", "NOTICE", "Record only friction that actually appeared. No speculative problem theatre.")
#step("04", "FIX", "Prefer the smallest mature repair: correct invocation, adapter, path, dependency, or owner handoff.")
#step("05", "REPEAT", "Run the original action again. A proposed fix is not a verified fix.")
#step("06", "REGISTER", "Preserve source, outputs, identity, provenance, consumption evidence, and relations.")

#pagebreak()

// 05 — NEGATIVE SPACE
#set page(fill: ink)
#set text(fill: paper)
#label("04 / DO NOT OVERBUILD")
#v(16mm)
#big("FRICTION")
#linebreak()
#big("IS NOT A")
#linebreak()
#text(size: 40pt, weight: "black", fill: ember)[FRAMEWORK REQUEST.]
#v(14mm)
#rule()
#v(7mm)
#text(size: 13pt)[
A broken command may need a flag.\
A missing dependency may need the declared environment.\
A bad handoff may need one adapter.\
A semantic mismatch may need a different owner.
]
#v(9mm)
#text(size: 8.5pt, fill: rgb("#bdbdbd"))[
The smallest adequate repair preserves attention for the work itself.
]

#pagebreak()
#set page(fill: paper)
#set text(fill: ink)

// 06 — REALITY LADDER
#label("05 / REALITY LADDER")
#v(12mm)
#big("EXISTS ≠ WORKS", s: 31pt)
#v(9mm)
#grid(columns: (1fr,), row-gutter: 4mm,
  box(stroke: 0.8pt + ink, inset: 7pt)[#text(size: 10pt, weight: "bold")[FILE EXISTS] #h(5pt) #text(size: 8.5pt)[— bytes are present]],
  box(stroke: 0.8pt + ink, inset: 7pt)[#text(size: 10pt, weight: "bold")[FORMAT VALID] #h(5pt) #text(size: 8.5pt)[— parser accepts it]],
  box(stroke: 0.8pt + ink, inset: 7pt)[#text(size: 10pt, weight: "bold")[CONSUMED] #h(5pt) #text(size: 8.5pt)[— target tool can actually use it]],
  box(stroke: 0.8pt + ink, inset: 7pt)[#text(size: 10pt, weight: "bold")[INSPECTED] #h(5pt) #text(size: 8.5pt)[— result is visibly / audibly / structurally coherent]],
  box(fill: acid, inset: 7pt)[#text(size: 10pt, weight: "bold")[USEFUL] #h(5pt) #text(size: 8.5pt)[— it serves the intended creative purpose]]
)
#v(10mm)
#text(size: 8pt, fill: graphite)[Each rung answers a different question. Do not let a lower rung impersonate a higher one.]

#pagebreak()

// 07 — EVIDENCE FROM A REAL WORK
#label("06 / DOGFOOD TRACE")
#v(11mm)
#text(size: 24pt, weight: "black")[A SONIC IDENT\
FOUND TWO SMALL TRUTHS.]
#v(9mm)
#box(fill: mist, inset: 8pt)[
  #text(size: 10pt, weight: "bold")[FFmpeg waveform rendering]
  #v(3pt)
  #text(size: 8.5pt)[A successful one-file image render still emitted an ambiguous sequence warning. The repair was not a new renderer: add the correct single-image invocation and verify the warning disappears.]
]
#v(6mm)
#box(fill: rgb("#ffe0d8"), inset: 8pt)[
  #text(size: 10pt, weight: "bold")[Python validation environment]
  #v(3pt)
  #text(size: 8.5pt)[Ambient Python lacked a project dependency. The repair was not a global install: run validation through the repository’s declared dependency environment.]
]
#v(10mm)
#text(size: 13pt, weight: "bold")[Tiny frictions. Real consequences. No mythology required.]
#v(4mm)
#text(size: 7pt, fill: graphite)[Source inspiration: existing Ordivon Media work `media:convergence-sonic-ident` and its recorded friction receipts.]

#pagebreak()

// 08 — BACK
#align(center + horizon)[
  #text(size: 8pt, weight: "bold", tracking: 0.16em)[ORDIVON CREATIVE WORKS]
  #v(8mm)
  #big("MAKE.", s: 34pt)
  #linebreak()
  #big("USE.", s: 34pt)
  #linebreak()
  #text(size: 34pt, weight: "black", fill: ember)[NOTICE.]
  #linebreak()
  #big("FIX.", s: 34pt)
  #v(11mm)
  #box(fill: acid, inset: 5pt)[#text(size: 9pt, weight: "bold")[FIELD NOTE 001 / FRICTION LOOP]]
]
#place(bottom + left)[#text(size: 7pt, fill: graphite)[Editable source: Typst · Delivery: PDF]]
