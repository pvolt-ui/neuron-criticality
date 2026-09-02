# Chokepoint Neurons Across Sensory Pathways — Progress Update

**Project 7, FlyWire Summer Internship 2026 · FAFB v783 connectome**

## The question

Which neurons are indispensable bottlenecks on the path from the senses (smell, touch,
vision) to the muscles, and are any of them bottlenecks for *more than one* sense — the
brain-wide critical hubs?

## What's done: Phase A + B (ranked bottlenecks, all three pathways) + Phase D (cross-modal)

For each of the three sensory modalities, we:

1. Built the **modality → descending** subgraph: every neuron within 2 synaptic hops of
   a sensory neuron of that modality *and* within 2 hops of reaching a descending
   (motor-command) neuron.
2. Computed **synapse-weighted betweenness centrality restricted to sensory-source →
   descending-target paths** (`networkx.betweenness_centrality_subset`), with edge
   distance = `1 / syn_count` so that strongly-connected pairs are "short". A neuron
   scores as a bottleneck only if the *strong* routes run through it.
3. Ranked every neuron; pulled the top 50 per modality and joined them to cell type,
   **neuropil**, neurotransmitter, and sub-class annotation.
4. Took the three top-50 lists and checked for neurons appearing in 2 or all 3.

### Data

Codex FAFB v783 **connections** export (`data/meta/fafb_connections.csv.gz`, fetched by
`download_connections.py`): 3,869,878 (pre, post, neuropil) rows carrying a synapse count,
which aggregate to 2,700,513 unique pairs over 134,181 neurons.

**Synapse threshold: ≥5 synapses per (pre, post) pair**, which is what Codex's standard
connections export ships. Stating it explicitly because it materially defines the graph.

### Subgraph sizes

| Modality | Sensory sources (in subgraph) | Descending targets | Subgraph nodes | Subgraph edges |
|---|---:|---:|---:|---:|
| Olfactory | 1,765 | 113 | 8,691 | 163,102 |
| Mechanosensory | 1,675 | 1,114 | 13,564 | 373,211 |
| Visual (photoreceptors) | 146 | 105 | 24,185 | 236,798 |

### Top bottleneck neurons, per pathway (validated set)

These describe the **validated top 25** — neurons in the top 25 by weighted betweenness
that also beat the degree-preserving null (Null B) at **FDR q ≤ 0.05**, 200 trials. Figures:
`fig4_validated_<modality>.png`. The raw top-50 composition is superseded; see the Null B
section for why.

**Olfactory (20/25 validated, median z = 12.1)** — antennal-lobe local interneurons
dominate (`lLN2T_c` ×4, `v2LN30`) plus the multiglomerular projection neuron
`MZ_lv2PN` and the serotonergic `AL-AST1`; 9 cholinergic, 4 GABAergic, 4 serotonergic.
**11 of the 20 sit in the antennal lobe** (`AL_L` 6, `AL_R` 5). The textbook anatomy
survives validation: the antennal lobe's local network is the first relay every olfactory
signal must cross, and it is a bottleneck by position rather than by connection count.
Caveat: `lLN2F_b`, named in earlier drafts, is 2/3 failed and drops out (see Null B).

**Mechanosensory (20/25 validated, median z = 11.8)** — descending neurons (`DNg62`,
`DNge132`) and central relays (`AN_GNG_89`, `CB0021`, `CB0109`); 11 cholinergic,
6 GABAergic. **14 of the 20 sit in the gnathal ganglion (`GNG`)** — the fly's
mechanosensory-to-motor integration centre. Touch/proprioception has a short
reflex-arc-like path to motor command, so the bottleneck is often the descending neuron
itself. This pathway is the study's strongest on every check: it is the only one whose
ranking is not substantially reproducible from synapse count (6/50 baseline overlap), and
it validates 43/50 against Null B under FDR correction — the full list, not just the top
half.

**Visual (24/25 validated, median z = 35.1)** — **validation moves the story out of the
medulla.** The raw top-50 was medulla-dominated (`ME_R` 12, `ME_L` 6); the validated top-25
leads with posterior slope and the gnathal ganglion (`IPS_R` 4, `IPS_L` 4, `GNG` 3,
`ME_R` 3, `ME_L` 3), with ocellar types (`OCG01d`, `OCG01e`) and `cM15`, `Sm41`;
15 cholinergic, 3 GABAergic, 3 glutamatergic. The medullar neurons ranked high largely on
connection count; what survives a degree-preserving shuffle is the *exit route* from the
optic lobe, not the optic lobe itself. Absolute betweenness remains ~2 orders of magnitude
below the other pathways (peak 1.1e-05 vs 8.9e-04) — the optic lobes are massively
parallel, with many redundant routes to the motor system — yet the z-scores are the
highest of the three (median 35.1), because in a graph that redundant, being on the strong
route at all is highly non-random.

Full ranked lists (`ranked_<modality>.csv`), annotated top-50s
(`characterized_<modality>.csv`), Null B verdicts (`null_degree_<modality>.csv`).

### Cross-modal overlap (Phase D — the payoff question)

Of the 150 modality-specific top-50 candidates, **five neurons appear in two modalities'
top-50. None appears in all three.**

| root_id | cell type | neuropil | NT | modalities |
|---|---|---|---|---|
| 720575940615723314 | PVLP076 | AVLP_R | ACH | mechanosensory + olfactory |
| 720575940626555440 | CB0478 | SAD | ACH | mechanosensory + visual |
| 720575940643112333 | CB0676 | SPS_R | ACH | mechanosensory + visual |
| 720575940624163303 | CB3916 | GNG | GABA | mechanosensory + visual |
| 720575940619636615 | PS124 | IPS_R | ACH | mechanosensory + visual |

**Honest read:** every shared bottleneck sits in a known convergence zone — gnathal
ganglion, subesophageal (`SAD`), posterior slope (`IPS`/`SPS`), anterior ventrolateral
protocerebrum (`AVLP`). That is a more coherent story than a scatter of unrelated cells:
cross-modal funnelling happens where the anatomy says it should, immediately upstream of
the descending system. But it is still *shallow* — five neurons out of 150 candidates,
none shared by all three senses, and four of the five pair mechanosensory with something
else. Convergence onto the motor system is mostly diffuse and modality-specific rather
than routed through a small set of master hubs.

## What changed from the previous (unweighted) run — and why it matters

The earlier version of this analysis ran **unweighted**, on a bare pre→post pair list
inherited from a different project that carried no synapse counts. Adding the real Codex
connections file changed the answer substantially:

| | Before | Now |
|---|---|---|
| Cross-modal bottlenecks | 1 (`DNp32`, olfactory+visual) | 5 (none olfactory+visual) |
| Olfactory top-50 retained | — | 15/50 |
| Mechanosensory top-50 retained | — | 18/50 |

**`DNp32` — the previous headline result — does not survive, and not marginally.** Its
weighted betweenness is *exactly zero* in both olfactory (rank 5046/8691) and visual (rank
5734/24185), and it does not enter the mechanosensory subgraph at all. Zero means it lies
on no shortest weighted sensory→descending path whatsoever. It was an artifact of treating
a weak connection as equal to a strong one.

Two things changed at once (the graph gained a ≥5-synapse threshold; the metric gained
weights), so `weighting_ablation.py` runs the *unweighted* metric on the *new* graph to
separate them. Weighting alone accounts for most of the turnover:

| Modality | top-50 changed by weighting alone |
|---|---:|
| Olfactory | 30/50 |
| Mechanosensory | 32/50 |
| Visual | 23/50 |

**Conclusion: synapse weighting is not a refinement, it decides the answer.** Roughly half
to two-thirds of each top-50 turns over. Any bottleneck claim from the unweighted run
should be treated as superseded.

## Does the metric matter? (metric agreement matrix)

`metric_matrix.py` computes every candidate importance metric on each subgraph and
measures agreement over intermediary neurons (`super_class == central`), scoring top-50
overlap against its hypergeometric chance expectation rather than raw counts — the visual
subgraph has 452 intermediaries and the olfactory 6,620, so the same overlap count means
very different things. Full matrix: `metric_agreement.txt`.

### Weighted betweenness vs trivial baselines — the uncomfortable one

| Modality | bw_weighted vs bw_unweighted | vs total_syn | chance expectation |
|---|---:|---:|---:|
| Olfactory | 18/50 | **23/50** | 0.38 |
| Mechanosensory | 17/50 | 6/50 | 0.31 |
| Visual | 30/50 | **26/50** | 5.53 |

**In olfactory, weighted betweenness agrees with raw synapse count *more* than it agrees
with its own unweighted version** (23/50 vs 18/50, rho = 0.47). Visual is nearly as bad
(26/50, rho = 0.54). For those two pathways, a large share of the bottleneck ranking is
recoverable by counting synapses — no path computation required. That has to be said out
loud, because "we ran betweenness centrality" implies the ranking contains something
degree cannot see, and for two of three pathways it substantially does not.

**Mechanosensory is the exception and is now the strongest pathway in the study.** Its
overlap with `total_syn` is 6/50 against 0.31 expected — above chance, but the ranking is
overwhelmingly *not* a synapse count. This inverts the earlier reading of the three
modalities: olfactory recovered textbook anatomy (antennal lobe) and looked like the clean
result, but "high-degree AL interneurons rank high" is close to a tautology. The
mechanosensory bottlenecks are the ones that required the metric.

### Adjusted influence is measuring something else entirely

Influence (Bates et al. 2025, `influence.py`) and weighted betweenness barely agree:
olfactory rho = **-0.003** with 1/50 top-50 overlap (p = 0.32, indistinguishable from
chance), mechanosensory rho = +0.25 with **0/50**, visual rho = +0.32 with 16/50.

This is not influence being noisy. Influence agrees strongly with the independent
probabilistic traversal model (19/50, 21/50, 35/50 overlap; rho 0.77–0.89) — the two
flow-based metrics agree with each other and jointly disagree with both betweenness and
every degree baseline. Two coherent camps, not one signal and one artifact:

- **path metrics** (betweenness, degree, synapse count) — who sits on strong routes
- **flow metrics** (influence, traversal) — who gets recruited early and broadly

Influence also correlates with hop distance from the sensory seed (rho = -0.29 olfactory,
-0.53 mechanosensory, -0.31 visual), so part of "influential" is just "close to the
source". `metric_comparison.py` stratifies by hop to control for this; the betweenness
correlation stays weak within each hop band.

**Consequence for the headline claim.** "These are the critical neurons" is not
metric-independent. The defensible statement is narrower: *these are the neurons on the
strongest sensory→motor routes*, and a flow-based definition of criticality selects a
largely disjoint set. Both belong on the poster.

## Are the cross-modal five real? (node-deletion test — no)

Betweenness says a neuron carries many shortest paths; it does not say the pathway would
suffer without it. `cross_modal_audit.py` deletes each neuron and re-solves all
sampled-source → descending-target weighted distances, against two control bands from the
same graph.

| Modality | candidate detour | top-50 control | rank-1000+ control |
|---|---:|---:|---:|
| Olfactory | 0.36% | 0.37% ± 0.34 | 0.000% |
| Mechanosensory | 0.02–0.06% | 0.34% ± 0.40 | 0.001% |
| Visual | 0.27–3.81% | 1.46% ± 2.50 | 0.000% |

**Not one of the five does more damage than an ordinary top-50 neuron of the same
pathway** (z = -0.79 to +0.94, every one inside the control distribution), and **none of
the five disconnects a single source→target pair**. Removing the single highest-ranked
visual bottleneck (`CB3916`, rank 1) lengthens the average strong route by 3.8%.

**Other neurons do disconnect pairs, though — the five simply aren't among them.** Three
of twelve mechanosensory top-50 controls, one mechanosensory rank-1223 control, and four of
twelve visual top-50 controls sever pairs. Every cut count is an exact multiple of the
target count (1114 mechanosensory, 105 visual), which means the unit being severed is a
whole **sensory source**: for a handful of individual mechanosensory and photoreceptor
neurons, one interneuron is the sole gateway to the entire descending system. Olfactory
never does this — no single deletion cuts anything there, consistent with the antennal
lobe's dense local network.

Two honest readings:

1. **The cross-modal five are not special among bottlenecks.** They are ordinary top-50
   neurons that happen to appear in two lists, and they are *less* damaging than several
   ordinary controls. The Phase D result is a co-occurrence, not evidence of privileged
   hubs.
2. **Single-neuron indispensability exists but is rare, peripheral, and not what
   betweenness ranks.** It shows up as individual sensory neurons losing their only route
   out, not as the pathway as a whole failing — and a rank-1223 neuron does it while the
   rank-1 visual bottleneck does not. So "bottleneck" in the betweenness sense means
   *carries much of the traffic*, not *is required*; the two are close to independent.

**Correction note.** An earlier version of this section claimed zero pairs were cut
anywhere. That was an artifact: deleting a neuron that is *itself* a sampled source or
descending target trivially kills every pair it is an endpoint of, and control draws hit
endpoints by chance while the interneuron candidates never did. Both scripts now score
damage only over pairs whose own endpoints survive the deletion (`damage(..., keep_src,
keep_tgt)`), which removes the artifact and leaves the genuine cuts above.

The rank-1000+ controls do register ~0.000%, so the ranking is not meaningless: top-50
neurons cause measurably more disruption than mid-ranked ones, by 2–3 orders of magnitude.
The gradient is real; the absolute stakes are low.

Cutoff-artifact check: all five sit at hop 2 from the nearest sensory source and hop 1 from
the nearest descending target. Top-50 controls average 1.7–2.1 and 0.5–1.3, so the
candidates sit at the source-side 2-hop boundary slightly more consistently than typical
bottlenecks — worth noting, but not a distinct failure mode, since the controls populate
the same boundary.

## The unit of criticality is the cell type, not the neuron

`celltype_ablation.py`. Single-neuron deletion barely dents the pathway, but fly neurons
come in bilateral pairs and cell-type cohorts, so that may only show that the other copy
covers the loss. This deletes an **entire cell type** — every copy, both hemispheres — from
each validated top-25 list and re-solves.

The control is the whole experiment: deleting 4 neurons always beats deleting 1, so every
cell type is scored against **size-matched random deletions**, both from ranks 1000–2000
(`random_mid`) and from the top 200 (`random_top`). Beating `random_top` means the effect
is about cohort *coherence*, not merely about deleting well-ranked neurons.

**Note: the comparison below is against the best *single copy*, which conflates cohort
size with cohort coherence — deleting 4 neurons beats deleting 1 for trivial reasons. The
cohort sweep in the next section makes the correct comparison (against the *sum* of the
individual damages) and the effect is much smaller than these ratios suggest. Read the two
sections together; the numbers here are kept because they are what the ablation measured.**

| Modality | cell type | copies | best single copy | whole type | z vs size-matched top-200 |
|---|---|---:|---:|---:|---:|
| Visual | `OCG01d` | 2 | 7.26% | **9.63%** | +15.9 |
| Olfactory | `v2LN30` | 2 | 3.52% | 4.98% | +13.0 |
| Olfactory | `MZ_lv2PN` | 2 | 1.61% | 3.01% | +7.5 |
| Olfactory | `lLN2T_c` | 4 | 0.39% | **4.38%** | +7.1 |
| Mechanosensory | `CB0109` | 2 | 1.02% | 1.26% | +7.6 |
| Mechanosensory | `DNge132` | 2 | 0.65% | 0.94% | +5.4 |
| Visual | `CB0415` | 2 | 1.55% | 3.42% | +5.2 |

`lLN2T_c` is the largest cohort in any validated list: its best single copy causes a 0.39%
detour, all four copies cause 4.38%. Against the *sum* of its four individual damages
(2.60%), however, the cohort effect is 1.68× — real, but far short of what the 11× headline
implies.

## Cohort sweep — how much of that is size, and how much is coherence?

`cohort_sweep.py` separates the two effects the ablation above confounded. It measures a
**size curve** (random sets of k = 1…32 from three rank bands), and scores every cell type
against random sets matched on **both size and rank band**, plus a superadditivity ratio
= cohort damage ÷ sum of its members' individual damages.

**Damage grows roughly linearly with the number of neurons removed.** Random top-200 sets,
mean detour %:

| Modality | k=1 | k=2 | k=4 | k=8 | k=16 | k=32 |
|---|---:|---:|---:|---:|---:|---:|
| Olfactory | 0.27 | 0.35 | 0.74 | 1.68 | 3.54 | 7.40 |
| Mechanosensory | 0.04 | 0.20 | 0.34 | 0.86 | 1.50 | 2.92 |
| Visual | 0.59 | 0.15 | 0.69 | 2.78 | 4.27 | 6.55 |

Roughly 0.23% per neuron in olfactory and 0.09% in mechanosensory, with no acceleration.
Mid- and low-ranked bands stay near zero at every size. (Visual is non-monotonic at small k
— its damage distribution is heavy-tailed and 10 draws is too few there.)

**Against the correct baseline, cell types are mostly additive.**

| Modality | superadditive (>1×) | median ratio | beat rank-matched control at z>2 |
|---|---:|---:|---:|
| Olfactory | 24/25 | 1.14× | 5/25 |
| Mechanosensory | 23/25 | 1.02× | 3/25 |
| Visual | 23/25 | 1.08× | 6/25 |

Nearly every cell type is superadditive, but **barely** — the median cohort exceeds the sum
of its parts by 2–14%, and only 14 of 75 types tested beat a size- and rank-matched random
set at z > 2. The honest conclusion is a substantially weaker version of the ablation
section's:

> Cell-type cohorts are **slightly** more than the sum of their neurons, and a minority are
> distinctly more. Most of what looked like a cohort effect in the ablation was simply the
> size of the deletion.

**The minority is real, though, and worth naming.** Types that are both strongly
superadditive and beat their rank-matched control:

| Modality | cell type | copies | superadd | z vs rank-matched |
|---|---|---:|---:|---:|
| Olfactory | `VA2_adPN` | 2 | 3.91× | +19.7 |
| Olfactory | `VM4_adPN` | 2 | 1.43× | +2.7 |
| Olfactory | `lLN2T_c` | 4 | 1.68× | +2.3 |
| Visual | `OCG02b` | 2 | 1.33× | +5.4 |
| Visual | `OCG01d` | 2 | 1.08× | +3.1 |
| Mechanosensory | `CB0109` | 2 | 1.04× | +2.8 |

`VA2_adPN` is the standout — a uniglomerular projection-neuron pair whose two copies
together do nearly 4× their individual sum, at 20 sd above comparable random pairs. Note
the irony: uniglomerular PNs were the group that *failed* Null B most consistently as
individuals. A neuron can be unremarkable alone and load-bearing as a pair, which is
precisely the case for reporting cohort effects separately rather than folding them into a
single "importance" score.

**Superadditivity and excess-over-control are largely independent.** `v2LN30` is only 1.02×
superadditive yet sits at z = +5.8; `PS124` is 4.35× superadditive at z = −0.6. The first
is a coherent pair that is no more than its parts; the second is more than its parts but no
more than any comparable pair. Both patterns are interesting and they are not the same
measurement.

**Cell types also cut pairs that single copies cannot.**

| Modality | types cutting ≥1 pair | single copies cutting ≥1 |
|---|---:|---:|
| Olfactory | 0/12 | 0/12 |
| Mechanosensory | 6/15 | 5/15 |
| Visual | 6/16 | 6/16 |

`AN_GNG_89` cuts 3,342 pairs as a type versus 1,114 for its best copy — three sensory
sources fully severed instead of one. `OCG01d` cuts 1,890 versus 1,050. The pattern holds
in mechanosensory and visual and is entirely absent in olfactory, which matches the
deletion-test result: the antennal lobe's local network has no single-gateway sources to
lose.

**Honest limits.** Most cohorts are bilateral pairs (k = 2), so for them "cell type" and
"both copies" are the same experiment. The sweep above covers k up to 43 for random sets
but real types with more than 4 well-ranked copies are scarce, so the coherence result
rests mostly on pairs. Rank-matched controls whose own damage is ~0 produce unstable
z-values (flagged `near-zero ctl` in the output and excluded from the counts above). All
damage is measured on the same 100 sampled sources used elsewhere.

## Null model (Null A — weight permutation)

`null_weight_permutation.py`, 50 trials per modality. Displacement = how far a weighting
moves the top-50 off the unweighted baseline.

| Modality | real weights | permuted weights | z | p |
|---|---:|---:|---:|---:|
| Olfactory | 31 | 25.3 ± 2.2 | +2.60 | 0.039 |
| Mechanosensory | 29 | 22.3 ± 2.3 | +2.97 | 0.020 |
| Visual | 23 | 15.6 ± 1.7 | +4.46 | 0.020 |

Real synapse weights displace the ranking further than randomly permuted weights drawn
from the same distribution, in all three pathways. **This validates the weighting, not the
neurons.** It says the reweighting is systematic rather than parameter noise; it does not
say any neuron is more of a bottleneck than a degree-preserving shuffle would produce.
That null is Null B, below.

## Null model (Null B — degree-preserving shuffle) — the top-50 survive

`null_degree_preserving.py`, **200 trials** × 100 sampled sources per modality. Directed
double-edge swap preserves every neuron's in-degree, out-degree and out-synapse total
exactly, and destroys only *which partners it has*. A neuron that keeps a high betweenness
under this null is a bottleneck **by position, not by connection count** — which is exactly
the objection the metric agreement matrix raised.

| Modality | above null (FDR q≤0.05) | top 25 | median z |
|---|---:|---:|---:|
| Olfactory | 37/50 | 20/25 | 5.3 |
| Mechanosensory | 43/50 | 20/25 | 6.4 |
| Visual | 45/50 | 24/25 | 19.9 |

**The result survives multiple-comparison correction essentially intact.** Testing 50
neurons per pathway at uncorrected p ≤ 0.05 would expect ~2.5 false positives on its own,
so the counts above are Benjamini-Hochberg FDR-corrected. Three details worth stating in a
methods section: the corrected and uncorrected counts are *identical* in all three
pathways (when effects are this large, correction barely bites); the empirical p floor is
now 1/(trials+1) = 0.005, where the earlier 20-trial run was quantised at 0.05 and could
not have survived correction at all; and no neuron has a null betweenness of exactly zero,
so the z-scores are not inflated by degenerate null distributions. An earlier 20-trial pass
reported 40/46/44 at uncorrected p — the drop to 37/43/45 is the honest cost of doing this
properly.

**This rescues the ranking from the degree critique.** The two findings are not in conflict:
across the whole population betweenness correlates with synapse count (rho ≈ 0.47–0.66),
but the specific top-ranked neurons score far above what their own degree predicts —
`MZ_lv2PN` at z = +50, and in visual `CB3916` at z = +140. Population-level degree
dependence, top-level positional signal.

**Report the top 25, not the top 50.** Survival degrades with rank; the bottom half of
each list carries most of the failures. The **validated set** used throughout this document
and in `fig4_validated_<modality>.png` is now defined as *rank ≤ 25 and FDR q ≤ 0.05*:
20 neurons olfactory, 20 mechanosensory, 24 visual.

**Named neurons that do not survive.** In olfactory, `lLN2F_b` appears three times in the
top 50 and **two of the three copies fail** (rank 23, z = -2.0, p = 1.00; rank 42,
z = -0.5). The third (rank 16) passes only marginally, at z = +2.1 — the weakest survivor
of any neuron named in the headline paragraph. The cell type should therefore be qualified
rather than struck: one copy is a genuine positional bottleneck, two are explained by
connectivity alone. The failing olfactory set is dominated by
uniglomerular projection neurons (`DM1_lPN`, `VA6_adPN`, `VL2a_adPN`, `VM6_adPN`), which is
biologically sensible: a uniglomerular PN is a high-throughput relay, not a chokepoint —
high betweenness by traffic volume, not by unavoidability. The local interneurons and the
multiglomerular `MZ_lv2PN` are what survive.

### Null B vs the deletion test: positioned but not indispensable

The cross-modal five pass Null B emphatically (`CB3916` z = +140 in visual, `CB0478`
z = +67) yet fail the deletion test entirely. That is not a contradiction, and the pair of
results is sharper than either alone:

- **Null B** asks *is this neuron's position non-random?* → yes, strongly.
- **Deletion** asks *does the pathway need it?* → no, not at all.

A neuron can sit at a genuinely structured, non-accidental junction and still be
dispensable, because a parallel route of comparable weight carries the load when it is
removed. **Structured redundancy**, not random redundancy. This is the most defensible
version of the project's headline: the fly's sensory→motor routing has real, identifiable
architecture at these junctions, and no single point of failure at any of them.

## Cross-dataset replication (MCNS) — the bottlenecks reproduce in a second animal

Every result above rests on FAFB v783: one brain, one individual, one sex. `prepare_mcns.py`
rebuilds the same three pathway subgraphs on the **Janelia male CNS (MCNS v0.9)**, which
differs on all three counts and additionally contains the ventral nerve cord.

**No new data access was needed.** Codex publishes weighted connection exports for MCNS,
MANC and BANC at the same base URL as FAFB's, under `connections_princeton.csv.gz`, with an
identical `pre_root_id, post_root_id, neuropil, syn_count, nt_type` schema. The local
`banc_626_edge_list.csv` / `mcns_0.9_edge_list.csv` files are unweighted pair lists — the
same defect that produced the false `DNp32` result — and are superseded by these.

MCNS was chosen over BANC because its `Class` vocabulary uses `olfactory` / `visual` /
`mechanosensory` directly, while BANC names sensory cells `<modality>_receptor_neuron` and
carries no mechanosensory class, so two of three pathways would need hand-built label
mappings. BANC remains the natural third dataset.

### Subgraph sizes, MCNS vs FAFB (descending endpoint)

| Modality | FAFB nodes / edges | MCNS nodes / edges | MCNS sources | MCNS targets |
|---|---|---|---:|---:|
| Olfactory | 8,691 / 163,102 | 12,788 / 409,149 | 2,615 | 197 |
| Mechanosensory | 13,564 / 373,211 | 52,116 / 2,526,868 | 5,421 | 2,002 |
| Visual | 24,185 / 236,798 | 45,794 / 977,533 | 254 | 71 |

MCNS is a substantially denser reconstruction (6.24M weighted pairs against FAFB's 2.70M).
Note the visual pathway thins to 254 sources under the 2-hop cutoff, mirroring FAFB's
146 — the same structural fact in a second animal, not a FAFB reconstruction artifact.

### Only mechanosensory reaches motor neurons

MCNS includes the VNC, so for the first time the pathway can be run to **real effectors**
rather than stopping at descending neurons. Rebuilding with `--endpoint motor`:

| Modality | sources in subgraph | motor targets |
|---|---:|---:|
| Olfactory | 1 | 1 |
| Mechanosensory | 4,961 | 696 |
| Visual | 0 | 0 |

**At a 2-hop cutoff, only mechanosensory reaches the motor system at all.** Olfactory and
visual signals are structurally further from the muscles than two synapses past a
descending neuron. This retroactively justifies FAFB's descending-neuron endpoint — it was
not an arbitrary convenience, it is the only endpoint the other two modalities *can* have
at this depth — and it independently corroborates the reflex-arc reading of the
mechanosensory pathway from the FAFB characterization.

### The bottleneck cell types replicate — all three pathways

`compare_datasets.py`. Root IDs are dataset-specific, so the comparison is at **cell-type**
level, which is also the level connectomics claims are normally made at. A type's score is
the max betweenness over its members (a type is a bottleneck if any copy is, and copy counts
differ between datasets). Chance expectation is hypergeometric over the vocabulary the two
datasets actually share.

| Pathway | shared types | top-25 overlap | expected by chance | p | Spearman ρ (all shared) |
|---|---:|---:|---:|---:|---:|
| Olfactory | 1,209 | **9** | 0.52 | 2.3e-10 | **+0.669** |
| Mechanosensory | 2,218 | **12** | 0.28 | 8.8e-19 | **+0.710** |
| Visual | 282 | **10** | 2.22 | 6.5e-06 | **+0.449** |

**This is the strongest result in the study.** Two different animals, different sexes,
different reconstruction pipelines, independently annotated — and the bottleneck rankings
agree at ρ ≈ 0.67–0.71 across *thousands* of shared cell types, with top-25 overlaps 17×,
43× and 4.5× their chance expectations. Whatever weighted betweenness is measuring on this
pathway, it is a property of the fly nervous system and not of one reconstruction.

Replicating types:

- **Olfactory** — `lLN2T_c`, `v2LN30`, `il3LN6`, `MZ_lv2PN`, `AL-AST1`, `DM1_lPN`, `PLP096`,
  `PVLP076`, `lLN2F_b`. The antennal-lobe local interneuron story reproduces in full.
- **Mechanosensory** — `DNg62`, `DNge132`, `DNge027`, `DNg35`, `DNg16`, `DNg100`, `DNp35`,
  `AVLP080`, `AVLP340`, `PS100`, `PS124`, `PVLP076`. Highest overlap of the three, and the
  descending-neuron-as-bottleneck pattern is preserved.
- **Visual** — `aMe12`, `aMe6a`, `aMe20`, `Li33`, `PS279`, `PS280`, `DNp12`, `DNb05`,
  `OA-AL2i1`, `PS124`. Note these are accessory-medulla and posterior-slope types, *not*
  the main medulla types — consistent with Null B moving the FAFB visual story out of the
  medulla. Two independent lines now say the same thing.

`PVLP076` replicates in two pathways and `PS124` in two — both members of the original
cross-modal five. They fail the deletion test as indispensable neurons but recur as
bottlenecks across animals, which is a more defensible version of the Phase D claim than
the original.

**One honest wrinkle.** `lLN2F_b` replicates strongly in MCNS despite 2 of 3 copies failing
Null B in FAFB. A type can be positioned consistently across animals while its individual
copies are explained by their degree — replication and degree-independence are different
questions, and this type separates them.

### The redundancy result replicates too

`replicate_robustness.py` reruns the deletion test on MCNS (15 neurons per band, same
endpoint-safe scoring).

| Pathway | top-50 mean detour | rank 1000–2000 | neurons cutting ≥1 pair |
|---|---:|---:|---:|
| Olfactory | 0.35% (max 0.90%) | 0.000% | 0/45 |
| Mechanosensory | 0.06% (max 0.23%) | 0.002% | 0/45 |
| Visual | 0.45% (max 3.01%) | 0.000% | 0/45 |

Both halves of the FAFB finding carry over: deleting a top-50 bottleneck costs **under 1%**
of route length on average (FAFB: 0.37 / 0.34 / 1.46%), and the gradient against mid-ranked
neurons is intact — top-50 damage is orders of magnitude above rank-1000+, which is
indistinguishable from zero. So "high betweenness means carries traffic, not required" is
not a FAFB artifact either.

**One thing does not replicate.** In FAFB, a few single deletions severed whole sensory
sources from the descending system (3 of 12 mechanosensory top-50 controls, 4 of 12 visual,
and one rank-1223 neuron). In the MCNS sample, **nothing cuts anything** — 0 of 45 tested
neurons in every pathway. The likely explanation is density: MCNS has 6.24M weighted pairs
to FAFB's 2.70M, so single-gateway sensory neurons are rarer. It may also be sampling — 15
neurons per band is a thin test for a phenomenon that hit ~25% of FAFB's top-50 controls.
Either way, the single-gateway phenomenon should be reported as FAFB-specific until it is
tested more thoroughly.

### Degree-independence replicates (olfactory and visual)

Null B rerun on MCNS (50 trials, `--root mcns`), against the 200-trial FAFB run:

| Pathway | FAFB top-50 (q_z) | MCNS top-50 (q_z) | FAFB top-25 | MCNS top-25 | FAFB med z | MCNS med z |
|---|---:|---:|---:|---:|---:|---:|
| Olfactory | 37/50 | 37/50 | 20/25 | 22/25 | 5.3 | 7.5 |
| Visual | 45/50 | 46/50 | 24/25 | 24/25 | 19.9 | 12.1 |

**Both pathways replicate within one or two neurons at every threshold.** `v2LN30` tops both
olfactory lists (MCNS z = 12.3, q = 1.9e-34). The degree-preserving result is therefore not
FAFB-specific: in two animals of different sex, the bottlenecks are positioned non-randomly
given their exact in-degree, out-degree and synapse totals.

At 50 trials the empirical p floor is 0.0196, so `q_emp` is the less sensitive statistic
(olfactory 32/50 vs `q_z` 37/50); `q_z` is the figure comparable to the 200-trial FAFB run.
Neither dataset has a neuron with an all-zero null distribution.

**Not attempted: mechanosensory.** One betweenness evaluation on the MCNS mechanosensory
subgraph (52k nodes, 2.53M edges) takes ~430 s, so 50 shuffles plus the edge-swap cost is
~6–8 h. It is the pathway where FAFB is already strongest (43/50), so the marginal value is
lowest. Null A, the cohort sweep and the metric agreement matrix also remain FAFB-only.

### Protocol note

Cross-dataset betweenness is being computed under a **shared sampled-source protocol**
(150 sources, `replicate_betweenness.py`) on both datasets. MCNS's mechanosensory subgraph
is too large for exact all-source betweenness, and comparing a full-source FAFB ranking
against a sampled MCNS one would confound the dataset difference with the protocol
difference — so FAFB is re-run sampled purely for this comparison
(`ranked_<modality>_sampled.csv`, which does not supersede `ranked_<modality>.csv`).

Only **cell types** are comparable across datasets; root IDs are dataset-specific.

## Ground truth: does the published physiology agree?

Every result above is internal to the connectome. The question that decides whether any of
it matters is whether a validated structural bottleneck corresponds to a neuron the fly
actually needs. This section is a **targeted literature check on the strongest validated
types, not a systematic screen** — the datasets themselves cannot answer it (BANC's
`Function` column annotates only sensory afferents; MCNS has none), so each claim below is
sourced.

### Olfactory: the physiology agrees with the *negative* result

`lLN2T_c` is the top-ranked, most-replicated, most-superadditive olfactory type in this
study. The published test of exactly that question:

> Selective silencing of synaptic transmission in the LN1 and LN2 multiglomerular GABAergic
> local interneuron populations — about a third of all antennal-lobe LNs — **did not
> significantly affect odor-evoked activity patterns**, neither glomerular input nor
> glomerular output, versus controls.
> ([Sci Rep 2017](https://www.nature.com/articles/s41598-017-08090-y))

This is a direct experimental match to the deletion test: `lLN2T_c` is a positioned,
degree-independent, replicating bottleneck whose removal costs 4.4% of route length and
disconnects nothing — and silencing its population does not measurably change olfactory
coding. **Two independent methods, one structural and one physiological, agree that a
structural bottleneck in the antennal lobe is not a functional requirement.**

Antennal-lobe LNs *are* implicated in gain control, with different stimulus features
recruiting different LN types at different sites
([Curr Biol 2023](https://www.sciencedirect.com/science/article/pii/S0960982223014422)) —
so the cells are not functionless. The claim they do not support is "indispensable relay".

### Mechanosensory: the anatomy agrees, and so does the redundancy

The GNG concentration (14 of 20 validated neurons) matches the established picture. The GNG
contains interneurons and descending neurons whose activation elicits head grooming, and
antennal mechanosensory input excites **parallel classes of descending neurons** organised
somatotopically
([eLife 2025](https://elifesciences.org/articles/108044),
[eLife 2023](https://elifesciences.org/articles/87602),
[Curr Biol 2024](https://www.sciencedirect.com/science/article/pii/S0960982224004433)).

Both halves of our mechanosensory result are corroborated: the pathway really is
GNG-centred and descending-neuron-terminated, *and* it is built from parallel pathways —
which is the anatomical reason single-neuron deletion does so little (0.06% mean detour in
MCNS).

### Visual: not verifiable at cell-type resolution

The ocellar pathway is implicated in flight and gaze stabilization via descending neurons
DNOVS1/2 and DNHS1
([J Neurosci 2017](https://www.jneurosci.org/content/37/14/3738)), which is consistent with
`OCG01b/d/e` ranking highly and with the validated set sitting on the optic-lobe *exit
route*. But **no functional characterization of `OCG01d` specifically could be verified**,
and the same holds for the `aMe12` / `PS279` / `PS280` types that replicate across datasets.
Reported as unresolved rather than as support.

### Pre-registered screen — the validated types are *not* better characterized

The check above searched where evidence was likely, which inflates apparent agreement.
`groundtruth_register.py` freezes the full type list *before* any searching, in two arms:

- **validated** — cell types of the validated top-25 (rank ≤ 25, Null B FDR q_z ≤ 0.05),
  pooled over pathways: 40 types (24 named, 16 placeholder `CB####`-style IDs).
- **control** — types drawn from betweenness ranks 1000–2000 of the same pathways, matched
  in count: 41 types (27 named, 14 placeholder).

The control arm is what makes the number mean anything. The fly literature is heavily
biased toward large, named, genetically accessible cells, and a centrality metric may
favour the same cells for unrelated reasons; the control measures that background rate.

| Arm | functional evidence found | anatomy only | not found | placeholder ID |
|---|---:|---:|---:|---:|
| Validated | **2** / 24 named | 1 | 21 | 16 |
| Control | **4** / 27 named | 0 | 23 | 14 |

**The validated bottlenecks are not better characterized than mid-ranked controls — they
are somewhat worse.** And the asymmetry in *kind* of evidence is sharper than the counts:

| Arm | type | verdict |
|---|---|---|
| Validated | `lLN2T_c` | silencing produced **no effect** on odor-evoked coding |
| Validated | `DNp10` | activation *sufficient* for reaching / wing flicking |
| Control | `T4a`, `T4c` | blocking makes flies **completely motion-blind** — necessity |
| Control | `Mi9` | silencing abolishes T4 direction selectivity — necessity |
| Control | `LC4` | activation *sufficient* for escape |

**All necessity-grade evidence in either arm sits in the control arm.** The single
validated type with a direct silencing test came back negative. So on the evidence
available, high weighted betweenness does not predict demonstrated functional necessity,
and the neurons that *are* known to be indispensable (T4, Mi9) sit at ranks 1000–2000 in
this metric.

This is consistent with everything else in the study rather than a surprise: T4 cells are
massively parallel and individually redundant on any single path, which is exactly the
configuration that scores low on betweenness and high on behavioural necessity when the
whole population is blocked. **Betweenness ranks traffic; necessity is a property of
populations.**

**Screen limitations, stated plainly.** Coverage came from 6 grouped literature searches,
not 51 independent per-type searches, so `not_found` means *this screen did not find it* —
not that no characterization exists. That biases both arms in the same direction, which is
why the arms are compared to each other rather than read as absolute rates. Placeholder IDs
are counted uncharacterized by construction. `AL-AST1` was left unresolved: the serotonergic
CSDn literature is probably the right match but the identity could not be confirmed, and
guessing it would have manufactured a hit in the validated arm.

### What this does and does not establish

- **Establishes:** the study's central negative claim is not an artifact of the metric or of
  graph surgery. Where the physiology has been done, it agrees that high-betweenness
  antennal-lobe interneurons are dispensable for the coding they sit on top of.
- **Establishes:** the mechanosensory anatomy and its parallel-pathway structure match the
  literature independently of this analysis.
- **Establishes (pre-registered screen):** betweenness rank does not predict demonstrated
  functional necessity. Validated types are no better characterized than rank-1000-2000
  controls (2/24 vs 4/27 named), and every necessity-grade result found sits in the control
  arm.
- **Does not establish:** that the validated bottlenecks are functionally unimportant. Most
  have never been tested; `not_found` is a statement about the literature's coverage and
  this screen's reach, not about the neurons.

## Honest scope / limitations

- **Visual endpoint coverage is now thin.** Under the ≥5-synapse threshold only 146
  photoreceptor sources and 105 descending targets survive into the visual subgraph (down
  from 481/163 unthresholded). The visual ranking rests on far fewer source–target pairs
  than the other two and should be read as the weakest of the three.
- **"Dominant neuropil" is a summary, not an absolute.** Across all 134,181 neurons the
  median neuron puts 79% of its synapses in its top neuropil, but within the top-50
  bottlenecks the median dominance is lower (olfactory 0.44, mechanosensory 0.66, visual
  0.47) — unsurprising, since bottleneck neurons are exactly the ones spanning regions.
  `neuropil_frac` is carried in the output so this is checkable per neuron.
- **2-hop cutoff.** 1 hop leaves too few real endpoints to be meaningful; 3 hops balloons
  past exact-betweenness feasibility. The cutoff is topological (2 synapses), independent
  of the synapse weighting.
- **The ranking is metric-dependent, and partly degree-driven.** See the agreement matrix
  above: flow-based metrics select a near-disjoint set, and in olfactory and visual a large
  share of the betweenness top-50 is recoverable from synapse count alone.
- **"Bottleneck" means high rank, not indispensable.** The deletion test puts a hard
  ceiling on the claim: no single neuron, at any rank, disconnects a single sensory→motor
  pair.
- **Two datasets now (FAFB v783 + MCNS v0.9).** Replicated in MCNS: the *ranking* (all three
  pathways, cell-type level), the *redundancy* result (all three pathways), and *Null B*
  (olfactory and visual). Still FAFB-only: Null B for mechanosensory (~6-8 h, not
  attempted), Null A, the cohort sweep, and the metric agreement matrix. BANC
  is available as a third dataset and needs a label mapping.
- **The single-gateway phenomenon is FAFB-only** — see the replication section. Do not state
  it as a general property of the fly connectome.
- **Null B uses sampled sources** (100 per modality, 20 trials) so that 60 shuffled-graph
  betweenness runs stay affordable. The sample is identical across real and null graphs so
  scores are comparable, but absolute values differ from the full-source run above.
- **Current-flow betweenness (Phase C) is not computationally feasible and has been
  abandoned.** `networkx.current_flow_betweenness_centrality_subset` ran for 24 hours on
  the *smallest* of the three subgraphs (olfactory, 8,691 nodes) without completing, at
  ~1 GB resident. The visual subgraph is 2.8x larger. Combined with the symmetrization
  problem — the metric requires an undirected graph, which lets signal run backwards from
  descending neurons to photoreceptors, inverting the sensory->motor question the study
  asks — this is reported as a negative feasibility result rather than pursued further.
  The traversal model in `metric_matrix.py` covers the flow-based family instead, at a
  fraction of the cost and without discarding edge direction.
- **Current-flow betweenness (Phase C) requires symmetrizing the graph**, which discards
  edge direction and lets signal run backwards from descending neurons to photoreceptors.
  It is being run for completeness because the proposal asked for it, but a directed
  sensory→motor question is not well served by an undirected metric, and it will be
  reported with that caveat rather than as a co-equal second opinion.

## What's next

1. **Poster build** — figures done (`fig1`-`fig4`); the replication result deserves its own
   panel and is not yet plotted.
2. ~~Current-flow (Phase C)~~ — abandoned as infeasible; see limitations.
3. **Lead with mechanosensory** for the metric argument (6/50 baseline overlap, 46/50 on
   Null B). Note the cohort effects are weakest there (median 1.02x, 3/25 beating control),
   so the cohort story belongs to olfactory and visual.
4. **Retire the cross-modal-hub framing.** Phase D's five neurons do not survive the
   deletion test. The replacement headline is the robustness result — sensory→motor routing
   has no single point of failure — which is a stronger and more defensible claim than five
   co-occurring neurons.
5. **Deepen the screen if it becomes a poster panel** — 51 per-type searches instead of 6
   grouped ones, and resolve `AL-AST1` against the CSDn literature.
6. Poster / presentation for end of August.

## Reproducing

```bash
python3 download_connections.py       # Codex FAFB v783 connections (50 MB)
python3 build_pathway_subgraphs.py    # weighted subgraphs, 3 modalities
python3 betweenness.py                # weighted betweenness  (~25 min)
python3 characterize.py               # cell type + neuropil + NT, figures
python3 cross_modal_overlap.py        # Phase D
python3 weighting_ablation.py       # weighting-vs-data attribution
python3 null_weight_permutation.py  # Null A: weight permutation (~40 min)
python3 influence.py                # adjusted influence (Bates et al. 2025)
python3 metric_comparison.py        # betweenness vs influence, hop-stratified
python3 metric_matrix.py [--no-current-flow]   # all metrics + agreement matrix
python3 cross_modal_audit.py        # node-deletion test on the cross-modal five
python3 null_degree_preserving.py   # Null B: degree-preserving swap (~25 min)
python3 celltype_ablation.py        # whole-cell-type deletion vs size-matched controls
python3 cohort_sweep.py             # size curve + rank-matched coherence test
python3 prepare_mcns.py [--endpoint motor]     # second connectome, same file contract
python3 replicate_betweenness.py --root . --suffix _sampled   # matched protocol, FAFB
python3 replicate_betweenness.py --root mcns                  # matched protocol, MCNS
python3 compare_datasets.py         # cell-type replication test
python3 poster_figures.py           # fig1-fig4, the poster figure set
```

Requires `networkx`, `pandas`, `matplotlib`, `scipy`.
