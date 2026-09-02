# Chokepoint Neurons Across Sensory Pathways

**FlyWire Summer Internship 2026, Project 7 — FAFB v783 + male CNS (MCNS v0.9) connectomes**

Which neurons carry the traffic on the way from the senses to the descending
(motor-command) neurons — and does the circuit actually depend on them?

For four sensory pathways (olfactory, mechanosensory, visual, ocellar) this
repository builds the modality → descending subgraph, ranks neurons by
synapse-weighted betweenness restricted to sensory-source → descending-target
paths, validates the ranking against null models, tests whether deleting the
top-ranked neurons actually damages the circuit, and checks whether any
bottleneck is shared across modalities. Everything is run in two connectomes,
so nothing counts unless it recurs in both animals.

## Headline findings

- **The rankings are anatomically coherent.** Olfactory bottlenecks are
  antennal-lobe local interneurons; mechanosensory ones sit in the gnathal
  ganglion and the descending neurons themselves; visual ones are the
  lobula-plate wide-field inhibitory network and the tangential output cells.
- **"Bottleneck" means high rank, not indispensable.** No single neuron, at any
  rank, disconnects a single sensory→motor pair when deleted. The graph routes
  around it.
- **Cross-modal convergence is shallow.** Of 200 top-50 candidates, six neurons
  appear in two pathways and none in three or more — all in known convergence
  zones (GNG, SAD, IPS/SPS, AVLP) immediately upstream of the descending system.
- **Rank is partly explained by degree.** Against a degree-preserving null,
  olfactory and mechanosensory validate strongly; the ocellar pathway does not —
  it is a small degree-driven reflex arc, not a positional-bottleneck story.
- **Selection bias is controlled for.** Because the top-50 is chosen for being
  extreme, the null-model test has a built-in winner's curse; the floor is
  measured by re-running the whole procedure on a shuffled graph treated as data.

Full results, caveats and the revision history are in **[RESULTS.md](RESULTS.md)**.
`RESULTS.pre-revision.md` keeps the superseded version — a mid-project review
found that the pathway originally called "visual" was in fact the ocellar
pathway; that correction and the selection-bias control changed several numbers.

## Method

1. **Subgraph** — every neuron within 2 synaptic hops of a sensory neuron of a
   given modality *and* within 2 hops of reaching a descending neuron. Synapse
   threshold ≥5 per (pre, post) pair (the Codex standard export).
2. **Betweenness** — `networkx.betweenness_centrality_subset` with edge distance
   `1 / syn_count`, so a neuron scores only if the *strong* routes run through it.
   Exact for olfactory / mechanosensory / ocellar; sampled-source (500 of 17,004,
   seed 0) for visual, where exact all-source betweenness is infeasible.
3. **Annotation** — cell type, neuropil, neurotransmitter, sub-class.
4. **Validation** — Null A (weight permutation), Null B (degree-preserving
   shuffle, FDR q ≤ 0.05), a Null B selection-bias control, alternative
   centrality metrics and an agreement matrix, and weighting ablations.
5. **Damage** — single-node and whole-cell-type deletion against size-matched
   controls; path-length and connectivity change rather than rank.
6. **Replication** — the whole protocol re-run on MCNS, compared at cell-type level.

Source definitions for every pathway live in `pathways.py` and are the single
source of truth; downstream scripts read the `is_source` column rather than
re-deriving sources.

## Repository layout

| | |
|---|---|
| `pathways.py` | pathway source definitions (single source of truth) |
| `download_connections.py`, `build_pathway_subgraphs.py`, `prepare_mcns.py` | data fetch and subgraph construction |
| `betweenness.py`, `influence.py`, `metric_matrix.py`, `metric_comparison.py` | centrality metrics and their agreement |
| `null_weight_permutation.py`, `null_degree_preserving.py`, `nullB_selection_control.py` | null models and the selection-bias floor |
| `cross_modal_overlap.py`, `cross_modal_audit.py` | shared bottlenecks and their deletion test |
| `celltype_ablation.py`, `cohort_sweep.py`, `weighting_ablation.py` | robustness and ablation |
| `replicate_betweenness.py`, `replicate_robustness.py`, `compare_datasets.py` | MCNS replication |
| `characterize.py`, `poster_figures.py`, `talk_figures.py` | annotation and figures |
| `RESULTS.md`, `QA.md`, `SCRIPT.md`, `TALK.md`, `ARIE.md` | write-up, symposium script and Q&A prep |

Ranked outputs are `ranked_<modality>.csv`, annotated top-50s
`characterized_<modality>.csv`, null verdicts `null_degree_<modality>.csv`.

## Data

Codex FAFB v783 connections export — 3,869,878 (pre, post, neuropil) rows
aggregating to 2,700,513 unique pairs over 134,181 neurons — plus MCNS v0.9.
**The bulk data files are not tracked in this repository** (they exceed GitHub's
file-size limits); `download_connections.py` fetches the FAFB connections file
and `prepare_mcns.py` builds the MCNS side.

## Reproducing

Requires `networkx`, `pandas`, `matplotlib`, `scipy`.

```bash
python3 download_connections.py       # Codex FAFB v783 connections (50 MB)
python3 build_pathway_subgraphs.py    # weighted subgraphs for all four pathways
python3 betweenness.py --modality olfactory mechanosensory ocellar   # exact (~25 min)
python3 betweenness.py --modality visual --sample 500                # sampled (~20 min)
python3 characterize.py               # annotation + figures
python3 cross_modal_overlap.py        # cross-modal shared bottlenecks
python3 null_weight_permutation.py    # Null A (~40 min)
python3 null_degree_preserving.py --trials 200        # Null B (olf/mech/ocellar)
python3 nullB_selection_control.py    # Null B selection-bias floor
python3 cross_modal_audit.py          # node-deletion test
python3 celltype_ablation.py          # cell-type deletion vs size-matched controls
python3 prepare_mcns.py               # second connectome
python3 replicate_betweenness.py --root mcns
python3 compare_datasets.py           # cell-type replication test
python3 poster_figures.py             # figure set
```

The full command list, including the metric matrix and cohort sweep, is in the
Reproducing section of `RESULTS.md`.

## Scope

This is an internship project, not a paper. The main limits: a 2-hop window on
each side, a metric-dependent ranking that is partly recoverable from synapse
count alone, sampled sources for the visual pathway, current-flow betweenness
abandoned as computationally infeasible, and several legacy-graph numbers still
flagged in `RESULTS.md` where the analysis has not been re-run. The limitations
section there is the honest and complete list.
