# Symposium Script — word-for-word, ~4:10 at 145 wpm

Matched slide-for-slide to `talk_concise.pptx` (5 slides). Audience: FlyWire /
PNI connectome community — DNs, FAFB/MCNS, betweenness, nulls all assumed.
Rule: memorize the first and last two sentences cold. Numbers in [brackets]
are cumulative time marks.

---

## Slide 1 — Title + hook [0:00–0:25]

Olfactory, mechanosensory and visual input all have to converge onto the
descending neurons — the one endpoint every modality reaches within two hops.
My question: on the way from the senses to the DNs, **which neurons carry the
traffic — and does the circuit actually depend on them?**

I asked this in two connectomes — FAFB and the male CNS — so nothing counts
unless it recurs in both animals.

## Slide 2 — The problem [0:25–1:00]

FAFB gives us the complete weighted graph, but not which neurons the
sensory-to-DN traffic depends on. So, three questions. **Which neurons rank
highest by synapse-weighted betweenness on sensory-to-DN paths**, per modality?
**Are any of them shared across modalities** — brain-wide hubs? And are they
**truly critical** — does deleting one lengthen or sever the paths, or does the
graph just route around it?

## Slide 3 — The solution [1:00–2:15]

*(gesture across the schematic)* One pathway graph per modality: sources on the
left, DNs on the right, everything within two hops of both in between. The
yellow cell is what I was hunting — the neuron the strong routes run through.

Three findings.

**One: every modality has these chokepoints, and they're the cells you'd
predict** — the antennal-lobe local network for olfaction, lLN2T_c and v2LN30;
gnathal descending neurons for mechanosensation; and for vision the wide-field
lobula-plate cells — LPi, Am1, H2.

**Two: they're conserved.** Rebuild everything in the male CNS — different
animal, different sex, different pipeline — and nine, twelve, and thirteen of
the top twenty-five cell types recur, against a chance expectation below one.

**Three — the headline — not one of them is required.** Delete any single
chokepoint and the strong routes lengthen by about half a percent. Nothing
disconnects. And cross-modal sharing is shallow: six of two hundred top neurons
span two modalities, none spans all three.

So: **structured but redundant** — conserved junctions carry the traffic, but
every one has a parallel route.

## Slide 4 — Does it hold up? [2:15–3:20]

The part I want you to trust. Every ranking was tested against
**degree-preserving nulls** at FDR five percent — is this just degree? Mostly
no. But I also ran a **selection-bias control**: the entire pipeline on a
shuffled graph treated as data, where every survivor is a false positive by
construction. That bounds the winner's curse — and it caught real inflation in
my own earlier numbers. Above that ceiling: **fifteen olfactory and two
mechanosensory neurons** positioned beyond any doubt.

And deletion damage spans **three orders of magnitude** — half a percent for a
top-fifty neuron, effectively zero at rank one thousand. The ranking is real;
the stakes are just low. Same answer in the second connectome.

## Slide 5 — Takeaway [3:20–4:10]

So: **conserved chokepoints, no single point of failure.** The broader point —
"critical" depends on which question you ask. Betweenness, deletion damage, and
cross-connectome conservation are three different measurements, and here they
disagree. T4 and Mi9 — behaviourally indispensable — sit at rank one thousand
in betweenness. **Necessity is a population property**, and cohort-level
deletions are exactly where this goes next.

The fly brain's sensory-motor chokepoints are real, they're conserved across
two connectomes — and you can cut any one of them without breaking anything.

*(stop — nothing after that sentence)*

---

## Delivery notes

- ~630 words → **4:10 at 145 wpm**, ~45 s of margin in the 5-minute slot.
- The selection-bias control (slide 4) is the differentiator for this audience
  — deliver "every survivor is a false positive by construction" at full pace.
- Owning the T4/Mi9 rank-1000 result turns your weakest point into the
  takeaway; faculty vote for people who understood their negative result.
- If running long, cut: the cross-modal sentence (slide 3) and "same answer in
  the second connectome" (slide 4). Never cut the closing sentence.
- Two-minute-warning fallback: slides 1 → 3 → closing sentence.
