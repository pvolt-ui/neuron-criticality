# Q&A Prep — symposium, likely questions with speakable answers

Answers are written to be said out loud in 15–30 seconds. Bold = the one
sentence to lead with. Backup slide references from talk.pptx (B1–B5).

---

## Methods choices

**Q1. Why descending neurons as the endpoint, and not motor neurons/muscles?**
**Because DNs are the only endpoint all three modalities share at this depth.**
In the male CNS, only mechanosensory reaches VNC motor neurons within the 2+2
hop window; olfactory reaches one and visual reaches zero. DNs are the common
funnel, so they make the pathways comparable. *(B5)*

**Q2. Why 1/synapses as edge distance?**
**Standard choice — strong connections are short.** I did test sensitivity:
weighting choice turns over 30–60% of each top-50, but real weights displace
the ranking more than permuted weights do, so the weights carry signal. Fair
criticism: I didn't test −log(p)-style distances. *(B2, Null A)*

**Q3. Why two hops on each side?**
**One hop leaves almost no real endpoints; three is computationally infeasible
for exact betweenness.** Two hops is the widest window where exact all-source
betweenness is tractable on the olfactory and mechanosensory graphs.

**Q4. Is the visual pathway exact?**
**No — sampled.** 500 of 17,004 sources, fixed seed, following the
sampled-source protocol; the graph is 60k nodes / 1.2M edges, where exact
all-source betweenness is infeasible. Olfactory, mechanosensory and ocellar
are exact. *(B1)*

**Q5. Why synapse threshold ≥5?**
That's what Codex's standard connections export ships — it materially defines
the graph, so I state it explicitly rather than pretend it's a free choice.

## Nulls and statistics

**Q6. Explain the selection-bias control again?**
**The top-50 are selected for being extreme, so they'd beat their own nulls
even in a structureless graph — winner's curse.** I ran the entire pipeline on
a degree-preserving shuffle treated as data: every "survivor" there is a false
positive by construction. That floor is ~16/50 in olfactory and ~34/50 in
mechanosensory — so I only claim neurons above the *maximum* z that selection
alone can manufacture: 15 olfactory, 2 mechanosensory. *(B2)*

**Q7. So most of your "validated" neurons could be selection artifacts?**
**Below the ceiling, individually — yes, that's exactly why I built the
control.** The FDR-survivor counts are honest but inflated; the
above-ceiling set is the defensible core. That correction is a result, not a
weakness — most betweenness studies never run it.

**Q8. Isn't 0.5% damage just because the graph is huge?**
**No — rank-1000 neurons give 0.001%.** The gradient between top-50 and
rank-1000 is three orders of magnitude, so the ranking is meaningful; it's the
absolute stakes that are low. And the same numbers replicate in the male CNS.
*(B3)*

**Q9. Does betweenness actually beat degree anywhere?**
**Mechanosensory, clearly: only 6 of its top-50 overlap a synapse-count
ranking** (chance ≈ 0.3). Olfactory and visual are largely degree-recoverable
(23/50, 26/50 overlap). And in replication, degree does slightly *better* —
so what's conserved is the pathway, not extra information betweenness sees.
I say that plainly because it's the honest read. *(B4, B5)*

## Interpretation

**Q10. If nothing is necessary, what did you actually find?**
**Structured redundancy — which is a positive claim about architecture.**
The chokepoints are real (non-random position, conserved across two brains),
but every one has a parallel route. Traffic, necessity, and conservation are
three different measurements, and showing they disagree tells you the
sensory-motor system is built like a resilient network, not a chain.

**Q11. T4/Mi9 are behaviourally essential but rank ~1000 — doesn't that mean
your metric misses what matters?**
**Yes — for single neurons, and that's the point.** T4 is a ~800-cell
population; no single T4 is a bottleneck, the *population* is. Betweenness
measures individual position, deletion measures individual necessity — and
behavioral necessity lives at the population level. That's exactly why
cohort-level deletions are the next step. *(B4)*

**Q12. Any cell types where the cohort IS more than the sum of its parts?**
Yes — 14 of 75 types beat size- and rank-matched random sets at z>2. The
standout is `VA2_adPN`: deleting the whole type does 3.9× the summed
single-neuron damage, z ≈ +20. Most types are barely superadditive
(median 1.02–1.14×). *(B3)*

**Q13. What about the six cross-modal neurons — are they special?**
Positionally shared, yes: `PVLP076` (olf+mech), `PS124` (mech+vis), two
`AVLP080` cells, `CB0677`, `CB0676`. But none spans all three modalities, and
none shows outsized deletion damage — shared position, not shared necessity.
*(B3)*

## Corrections / rigor

**Q14. What happened with the visual pathway?** *(Arie and mentors know —
answer without flinching)*
**The original "visual" sources (`class == visual`) turned out to be 142
ocellar photoreceptors plus only 4 compound-eye cells** — so the ranking was
an ocellar reflex arc with a medulla halo. I renamed it `ocellar`, rebuilt a
spec-compliant visual pathway from lamina/medulla columnar inputs (17k
sources), and withdrew the earlier visual replication claim because it compared
ocellar against R7/R8 sources. The corrected visual top-25 is clean motion
vision: LPi, Am1, H2, CT1, lobula tangentials. *(B1)*

**Q15. Is the ocellar pathway a bottleneck story then?**
No — on the pure 386-node ocellar graph, Null B survival drops to 13/50 and
the OCG01 cells sit at z ≈ 0: their rank is explained by degree. It's a real,
small reflex arc, but degree-driven, not positional. *(B1)*

## Bigger picture

**Q16. Does this generalize beyond the fly?**
Two data points say the architecture is conserved across two individuals (and
sexes) of one species. The natural next test is BANC or another species'
connectome. The design — rank, null, selection control, delete, replicate — is
connectome-agnostic.

**Q17. Functional predictions? Could someone test this experimentally?**
**Yes — the prediction is that silencing any single validated chokepoint
should NOT abolish behavior.** The one validated type already tested
(`lLN2T_c` / LN2 silencing) showed no effect on odour coding — consistent with
the deletion result. The sharper prediction: population-level silencing of a
superadditive cohort like `VA2_adPN` should hurt disproportionately. *(B4)*

**Q18. Why not current-flow betweenness / random-walk metrics?**
I tried. Current-flow was infeasible (>24 h with no result on the *smallest*
graph) and requires symmetrising a directed graph. I did compare flow-style
metrics (Bates influence, probabilistic traversal): they agree with each other
(ρ 0.77–0.89) but not with betweenness (ρ ≈ 0–0.3) — path-based and flow-based
"importance" pick different neurons, which is part of the "critical depends on
the question" takeaway. *(B4)*

---

## Delivery reminders

- Answer the question asked, in ≤30 s, ending on a period — don't trail off.
- For Q7/Q11/Q14 (the "gotcha" questions): agree first, then reframe — "Yes,
  and that's exactly why…". Never defensive.
- If you don't know: "I didn't test that — it's a good next analysis." Full
  stop. That answer wins points at PNI.
- Have talk.pptx open to backup slides B1–B5 for screen-share if a question
  goes deep.
- The dinner sentence, use it once if any answer allows: "It's built the way
  we build the internet — no single point of failure."
