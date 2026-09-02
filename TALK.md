# Symposium talk — 5 slides · 3:05 tight, 4:15 full

**Deck:** `talk.pptx` · rebuild with `python3 talk_figures.py && python3 make_talk.py`
Backups B1–B5 follow slide 5. Body text is 16–18 pt throughout.

---

## Elevator pitch (one sentence)

> This project maps where smell, touch and vision funnel toward the fly's motor system
> in two whole-brain connectomes, and finds conserved chokepoint neurons that carry the
> traffic but — because every one has a parallel route — none the circuit cannot live
> without.

**Hallway version (10 s):** *"The fly brain's sensory-to-motor chokepoints show up in
two connectomes — they're real, they're conserved, and you can cut any one of them
without breaking anything."*

---

# TALKING POINTS

Cue-card form: one line ≈ one sentence out loud. Bold = must say. Everything else is
droppable if you're running long.

## Slide 1 — The question · 0:30

- **Every signal from the fly's nose, antennae or eyes has to reach the descending
  neurons — the ~1,300 cells that carry commands to the body.**
- **Three questions: which neurons sit on the strongest routes from each sense; are any
  shared between senses; and does the circuit actually depend on them?**
- Two whole-brain connectomes: FlyWire FAFB, and the Janelia male CNS as a replication.
- *Don't* read the question box — it's there for people reading, not listening.

## Slide 2 — The main result · 1:20  ← the slide that matters

- *(gesture across the schematic, left to right)* **This is one pathway graph: sensory
  neurons on the left, descending neurons on the right, everything within two synapses
  of both in the middle. The yellow cell is the target — the neuron most of the strong
  routes run through.**
- **Three findings.**
- **One — every sense has them, and they land where the anatomy says they should:**
  antennal-lobe interneurons for smell, gnathal-ganglion descending neurons for touch,
  and for vision the wide-field cells of the lobula plate.
- **Two — they're conserved. Rebuild the whole thing in a second brain — different
  animal, different sex, different reconstruction pipeline — and 9, 12 and 13 of the top
  25 cell types come back, against a chance expectation below one.**
- Honest caveat: a plain synapse-count ranking replicates about as well, so what's
  conserved is the pathway, not something extra that betweenness sees.
- **Three — and this is the headline — none of them is required. Delete any one and the
  strong routes get about half a percent longer. Nothing disconnects.**
- Cross-modal sharing is shallow too: six neurons out of two hundred appear in two
  senses, none in all three.
- **So: structured but redundant. These are real, conserved junctions that carry the
  traffic — but every one has a parallel route. "Bottleneck" means carries the load, not
  required.**

## Slide 3 — How · 0:50

- **Build one graph per sense — every neuron within two synapses of a sensory input and
  two of a descending neuron — and rank by synapse-weighted betweenness, so a neuron
  scores only if the *strong* routes go through it.**
- **Then test it two ways.** Shuffle the wiring while keeping every neuron's exact
  degree: is the ranking just connection count?
- **And — the part worth pausing on — control the test itself.** Run the whole procedure on
  a structureless graph, where every "significant" neuron is a false positive by
  construction, to see how many survivors pure selection invents.
- **Then break it:** delete each bottleneck and re-solve every sensory-to-motor route.
- If pressed for time, drop the last bullet on the slide (scale/reproducibility).

## Slide 4 — Evidence · 0:50

- *(left panel)* **Each dot is one top-50 neuron, scored against a null that keeps its
  exact wiring statistics but shuffles who it talks to.** Most clear the usual
  significance bar.
- **But the dotted line is the highest score that pure selection can invent — measured
  by running the same test on a structureless graph. Only the neurons above it are
  positioned beyond doubt: fifteen in olfactory, two in mechanosensory.**
- *(top right)* **Deletion: about half a percent, and rank-1000 neurons are flat zero —
  so the ranking is real, the stakes are just low.** Same result in the second animal.
- *(bottom right)* Replication — solid bars betweenness, hatched degree. Degree does
  slightly better, which is the honest read.

## Slide 5 — Takeaway · 0:40

- **Conserved chokepoints, no single point of failure.**
- **"Critical" depends entirely on which question you ask. Traffic, necessity and
  conserved identity are three different measurements — and they disagree.**
- Two self-corrections along the way: the first "visual" pathway turned out to be the
  ocellar reflex arc, and the degree null was over-counting survivors until the
  selection control caught it.
- **Next: population-level deletions — that's where necessity actually lives. The cells
  known to be behaviourally essential, T4 and Mi9, sit at rank 1000 in this metric.**
- Stop on the pitch sentence. Don't add anything after it.

---

## Delivery notes

- **Timing, measured at 145 wpm: 4:15 if you say every bullet, 3:05 if you say only
  the bold ones.** Rehearse the bold-only version first — that's your safe talk, and the
  rest is what you add if the room is with you. Slide 2 is a third of it either way;
  that's deliberate, it's the result.
- If AV eats time: cut slide 3 to its first bullet and go straight to slide 4.
- If you get the two-minute warning: skip slide 4 entirely, jump to slide 5. Slides 1, 2
  and 5 are a complete talk on their own.
- Don't apologise for the caveats — state them flatly and move on. They read as rigor
  when delivered at the same pace as everything else, and as doubt when you slow down.

## Backups
B1 pathway definitions, sizes, the ocellar correction · B2 Null B + selection control ·
B3 deletion, cohorts, cross-modal six · B4 metric dependence + literature screen ·
B5 replication detail

## Likely questions
- **Why descending neurons, not muscles?** In the male CNS only mechanosensory reaches
  VNC motor neurons within the hop window; olfactory and visual reach one and zero. It's
  the only endpoint all three senses share at this depth.
- **Why 1/synapses as distance?** Standard choice. Weighting turns over 30–60 % of each
  top-50, and real weights displace the ranking more than permuted ones. Not
  sensitivity-tested against −log(p) — fair criticism.
- **Why two hops?** One leaves almost no real endpoints; three is computationally
  infeasible for exact betweenness.
- **Is the visual pathway exact?** No — 500 sampled sources of 17,000. The other
  pathways are exact.
- **Does betweenness beat degree anywhere?** Mechanosensory, clearly: only 6 of its
  top-50 overlap a synapse-count ranking. That's the pathway that needed the metric.
- **Isn't 0.5 % just because the graph is huge?** No — rank-1000 neurons give 0.001 %.
  The gradient is three orders of magnitude; the absolute stakes are what's low.
