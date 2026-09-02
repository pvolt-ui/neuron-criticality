#!/usr/bin/env python
"""
metric_comparison.py -- do betweenness and adjusted influence identify the same
neurons? And if not, is the disagreement real or an artifact?

WHY THIS IS NOT A FAIR FIGHT BY DEFAULT
---------------------------------------
Bates et al. (2025) state plainly that adjusted influence "is essentially a
computationally efficient and deterministic method of estimating the effective
number of hops separating the seed and the target." If influence is largely a
distance measure, then finding that it disagrees with betweenness is close to
trivial -- distance is not intermediacy, and neurons one hop from a sensory
neuron will score high on influence and near-zero on betweenness by construction.

So a raw correlation over all neurons proves nothing. This script runs four
increasingly strict comparisons:

  1. RAW           every non-seed neuron. The naive comparison.
  2. IS IT DISTANCE?  correlate influence against hop distance from the seed
                   set. If |rho| is high, influence largely *is* distance, and
                   comparison 1 is unfair to it.
  3. INTERMEDIARIES ONLY  restrict to central neurons -- drop sensory and
                   descending endpoints, keeping only cells that could be
                   bottlenecks at all.
  4. HOP-STRATIFIED  correlate within each hop-distance shell separately. This
                   is the decisive test: neurons equidistant from the seed, so
                   distance cannot explain any disagreement that remains.

If the metrics still disagree in (4), the disagreement is real and about what
the metrics measure, not about where the neurons sit.

Output: metric_comparison.txt, influence_<modality>.csv
"""
import os

import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

import influence as inf

ROOT = os.path.dirname(os.path.abspath(__file__))
CONNECTIONS = os.path.join(ROOT, "data", "meta", "fafb_connections.csv.gz")
from pathways import MODALITIES, source_ids  # noqa: E402
DESCENDING = {"descending", "motor"}
TOP_N = 50


def whole_brain_input_totals():
    """N_i = total input synapses onto each neuron, across the WHOLE brain.

    Normalizing within the subgraph would inflate weights for cells whose real
    input mostly arrives from outside it.
    """
    conn = pd.read_csv(CONNECTIONS, usecols=["pre_root_id", "post_root_id", "syn_count"])
    full = conn.groupby(["pre_root_id", "post_root_id"], as_index=False, sort=False)["syn_count"].sum()
    return full.groupby("post_root_id")["syn_count"].sum()


def hop_distance(edges, seeds):
    """Unweighted hop distance from the seed set, following edge direction."""
    G = nx.from_pandas_edgelist(edges, "source", "target", create_using=nx.DiGraph)
    seeds = [s for s in seeds if s in G]
    d = nx.multi_source_dijkstra_path_length(G, seeds, weight=lambda u, v, e: 1)
    return d


def spear(a, b):
    if len(a) < 10 or np.std(a) == 0 or np.std(b) == 0:
        return float("nan"), len(a)
    return spearmanr(a, b)[0], len(a)


def main():
    Ni = whole_brain_input_totals()
    lines = ["Betweenness vs adjusted influence", "=" * 60, ""]

    for m in MODALITIES:
        print(f"\n=== {m} ===")
        edges = pd.read_csv(os.path.join(ROOT, f"subgraph_edges_{m}.csv"))
        nodes = pd.read_csv(os.path.join(ROOT, f"subgraph_nodes_{m}.csv"))
        bw = pd.read_csv(os.path.join(ROOT, f"ranked_{m}.csv"))

        edges["norm"] = edges["syn_count"] / edges["target"].map(Ni)
        W, index, ids = inf.build_W(edges["source"], edges["target"], edges["norm"])

        seed_ids = set(source_ids(nodes, m))
        seed = [index[i] for i in seed_ids if i in index]
        sil = [index[i] for i in nodes.loc[(nodes.super_class == "sensory")
                                           & (nodes["class"] != m), "root_id"] if i in index]
        print(f"  {W.shape[0]} neurons  seed {len(seed)}  silenced {len(sil)}")

        r = inf.influence(W, seed, sil)
        df = pd.DataFrame({"root_id": ids, "influence": r, "adjusted": inf.adjusted(r)})
        df = df.merge(nodes, on="root_id", how="left").merge(bw, on="root_id", how="left")

        hops = hop_distance(edges, seed_ids)
        df["hops"] = df["root_id"].map(hops)
        df.to_csv(os.path.join(ROOT, f"influence_{m}.csv"), index=False)

        d = df[~df.root_id.isin(seed_ids)].dropna(subset=["betweenness", "adjusted"])

        rho_raw, n_raw = spear(d.adjusted, d.betweenness)
        rho_dist, _ = spear(d.adjusted, d.hops.fillna(-1))
        mid = d[d.super_class == "central"]
        rho_mid, n_mid = spear(mid.adjusted, mid.betweenness)

        top_i = set(d.nlargest(TOP_N, "adjusted").root_id)
        top_b = set(d.nlargest(TOP_N, "betweenness").root_id)
        top_i_mid = set(mid.nlargest(TOP_N, "adjusted").root_id)
        top_b_mid = set(mid.nlargest(TOP_N, "betweenness").root_id)

        lines += [
            f"--- {m} ---",
            f"  neurons compared (non-seed)        {n_raw}",
            f"  1. RAW           rho = {rho_raw:+.3f}   top-{TOP_N} overlap {len(top_i & top_b)}/{TOP_N}",
            f"  2. IS IT DISTANCE?  rho(influence, hops) = {rho_dist:+.3f}",
            f"  3. INTERMEDIARIES  rho = {rho_mid:+.3f}   top-{TOP_N} overlap "
            f"{len(top_i_mid & top_b_mid)}/{TOP_N}   (n={n_mid})",
            "  4. HOP-STRATIFIED",
        ]
        for h in sorted(x for x in d.hops.dropna().unique() if x <= 4):
            s = d[d.hops == h]
            rho_h, n_h = spear(s.adjusted, s.betweenness)
            lines.append(f"       hop {int(h)}:  rho = {rho_h:+.3f}   (n={n_h})")
        lines.append("")
        print("\n".join(lines[-8:]))

    summary = "\n".join(lines)
    with open(os.path.join(ROOT, "metric_comparison.txt"), "w") as f:
        f.write(summary + "\n")
    print("\n" + summary)


if __name__ == "__main__":
    main()
