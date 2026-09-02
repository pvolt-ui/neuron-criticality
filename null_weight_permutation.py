#!/usr/bin/env python
"""
null_weight_permutation.py -- Null A: does synapse weighting carry information,
or would ANY reweighting disturb the bottleneck ranking just as much?

THE CLAIM UNDER TEST
--------------------
weighting_ablation.py showed that switching from unweighted to synapse-weighted
betweenness replaces 23-32 of each top-50. The obvious rebuttal is that this is
mere parameter sensitivity: perturb any edge distances and the ranking reshuffles.
That would make the result noise, not a finding.

THE NULL
--------
Keep the topology and the weight *distribution* exactly as they are; destroy only
the correspondence between them, by permuting syn_count across edges. Real weights
sit where the biology put them; permuted weights have the same heavy tail but are
uncorrelated with structure.

THE STATISTIC
-------------
How far does weighting displace the ranking away from the unweighted baseline?

    displacement = 50 - |top50(weighted) & top50(unweighted)|

Computed once with the real weights, then N times with permuted weights.

    real displacement INSIDE the null distribution
        -> real weights are no more informative than random ones; claim fails.
    real displacement ABOVE the null distribution
        -> real weights reroute paths systematically, not randomly; claim holds.

COMPUTE
-------
Cost is one Dijkstra per source, so it scales with the number of sources. The
full olfactory subgraph (1,765 sources) takes ~7 min per betweenness run, which
is too slow to repeat N times -- so sources are subsampled. The SAME sampled
source set is used for the real run, the unweighted baseline, and every null
trial, so the comparison stays like-for-like. Defaults (200 sources, 30 trials)
land around 25 minutes.

Usage:
  python3 null_weight_permutation.py [--modality olfactory] [--sources 200]
                                     [--trials 30] [--seed 0]

Output:
  null_weight_permutation_<modality>.txt
"""
import argparse
import os
import time

import networkx as nx
import numpy as np
import pandas as pd

from pathways import source_ids  # noqa: E402

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
DESCENDING_CLASSES = {"descending", "motor"}
TOP_N = 50


def top_set(bc, n=TOP_N):
    """Top-n root_ids by betweenness, ties broken by root_id for determinism."""
    ranked = sorted(bc.items(), key=lambda kv: (-kv[1], kv[0]))
    return {rid for rid, _ in ranked[:n]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modality", default="olfactory")
    ap.add_argument("--sources", type=int, default=200,
                    help="number of sensory sources to sample (0 = use all)")
    ap.add_argument("--trials", type=int, default=30)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    m = args.modality

    edges = pd.read_csv(os.path.join(OUT_DIR, f"subgraph_edges_{m}.csv"))
    nodes = pd.read_csv(os.path.join(OUT_DIR, f"subgraph_nodes_{m}.csv"))

    G = nx.from_pandas_edgelist(
        edges, source="source", target="target",
        edge_attr="syn_count", create_using=nx.DiGraph,
    )
    G.add_nodes_from(nodes["root_id"])

    all_sources = sorted(set(source_ids(nodes, m)) & set(G))
    targets = set(nodes.loc[nodes["super_class"].isin(DESCENDING_CLASSES), "root_id"]) & set(G)

    if args.sources and args.sources < len(all_sources):
        idx = rng.choice(len(all_sources), size=args.sources, replace=False)
        sources = {all_sources[i] for i in sorted(idx)}
    else:
        sources = set(all_sources)

    print(f"=== {m} ===")
    print(f"  {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print(f"  sources: {len(sources)} of {len(all_sources)}   targets: {len(targets)}")
    print(f"  trials: {args.trials}   seed: {args.seed}")

    def betweenness(weight):
        return nx.betweenness_centrality_subset(
            G, sources=sources, targets=targets, normalized=True, weight=weight
        )

    # --- baseline: unweighted, on the same sampled sources ---
    t0 = time.time()
    top_unweighted = top_set(betweenness(None))
    per_run = time.time() - t0
    print(f"  unweighted baseline done ({per_run:.0f}s/run)")
    print(f"  estimated total: {per_run * (args.trials + 1) / 60:.0f} min")

    # --- observed: real synapse weights ---
    edge_list = list(G.edges())
    real_counts = np.array([G[u][v]["syn_count"] for u, v in edge_list], dtype=float)

    nx.set_edge_attributes(
        G, {e: 1.0 / c for e, c in zip(edge_list, real_counts)}, "distance"
    )
    top_real = top_set(betweenness("distance"))
    obs_overlap = len(top_real & top_unweighted)
    obs_disp = TOP_N - obs_overlap
    print(f"  REAL weights: overlap {obs_overlap}/{TOP_N}  -> displacement {obs_disp}")

    # --- null: permuted weights, same distribution, same topology ---
    null_disp = []
    for t in range(args.trials):
        permuted = rng.permutation(real_counts)
        nx.set_edge_attributes(
            G, {e: 1.0 / c for e, c in zip(edge_list, permuted)}, "distance"
        )
        d = TOP_N - len(top_set(betweenness("distance")) & top_unweighted)
        null_disp.append(d)
        print(f"    trial {t + 1:3d}/{args.trials}  displacement {d}", flush=True)

    null_disp = np.array(null_disp)
    mean, sd = null_disp.mean(), null_disp.std(ddof=1)
    z = (obs_disp - mean) / sd if sd > 0 else float("nan")
    # one-sided: how often does a random reweighting displace at least as much?
    p = (np.sum(null_disp >= obs_disp) + 1) / (len(null_disp) + 1)

    lines = [
        f"Null A -- weight permutation ({m})",
        "=" * 52,
        "",
        f"graph            {G.number_of_nodes()} nodes, {G.number_of_edges()} edges",
        f"sources          {len(sources)} of {len(all_sources)} (seed {args.seed})",
        f"targets          {len(targets)}",
        f"trials           {args.trials}",
        "",
        "Displacement = 50 - overlap(top50 weighted, top50 unweighted).",
        "How far a weighting moves the ranking off the unweighted baseline.",
        "",
        f"REAL weights     {obs_disp}",
        f"permuted weights {mean:.1f} +/- {sd:.1f}   (range {null_disp.min()}-{null_disp.max()})",
        "",
        f"z = {z:+.2f}    p = {p:.4f}  (one-sided: null displaces >= real)",
        "",
    ]
    if p < 0.05:
        lines += [
            "READ: real synapse weights displace the bottleneck ranking FURTHER than",
            "randomly permuted weights of the same distribution. The reweighting is",
            "systematic, not parameter noise -- the weighting result stands.",
        ]
    else:
        lines += [
            "READ: randomly permuted weights displace the ranking about as much as the",
            "real ones. On this evidence the weighting effect is NOT distinguishable",
            "from generic sensitivity to edge distances. Do not claim weighting carries",
            "biological signal without a stronger test.",
        ]

    summary = "\n".join(lines)
    print("\n" + summary)
    out = os.path.join(OUT_DIR, f"null_weight_permutation_{m}.txt")
    with open(out, "w") as f:
        f.write(summary + "\n")
    print(f"\nsaved {out}")


if __name__ == "__main__":
    main()
