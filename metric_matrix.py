#!/usr/bin/env python
"""
metric_matrix.py -- compute every candidate "importance" metric on each pathway
subgraph and measure how much they agree.

The point is not to crown a winner. It is to establish how much the choice of
metric determines which neurons get called important, and -- critically -- to
check whether the sophisticated metrics beat trivial baselines at all. If
in-degree reproduces the betweenness ranking, then betweenness is an expensive
way to count edges and should be reported as such.

METRICS
  bw_weighted      shortest-path betweenness, distance = 1/syn_count   (Phase A/B)
  bw_unweighted    shortest-path betweenness, all edges equal
  influence        adjusted influence, Bates et al. 2025               (influence.py)
  current_flow     current-flow betweenness -- REQUIRES SYMMETRIZING the graph,
                   which discards edge direction. Reported for completeness and
                   because the proposal asked for it, but a symmetrized
                   sensory->motor graph lets signal run backwards from motor
                   neurons to photoreceptors, so treat it with suspicion.
  traversal        probabilistic information-flow model: a neuron is recruited
                   with probability = (synapses from already-recruited cells) /
                   (its total input synapses), iterated to convergence and
                   averaged over runs. Reported as -mean recruitment step, so
                   higher = recruited earlier = more "important".
  in_syn/out_syn/total_syn, in_deg/out_deg   trivial baselines

AGREEMENT
  Spearman rho over intermediary neurons only (super_class == central), plus
  top-50 overlap normalized against its hypergeometric chance expectation.
  Raw overlap counts are not comparable across pathways -- the visual subgraph
  has ~450 intermediaries and the olfactory ~6,600, so the same count means
  very different things.

Output: metric_matrix_<modality>.csv, metric_agreement.txt
"""
import os
import sys

import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import hypergeom, spearmanr

ROOT = os.path.dirname(os.path.abspath(__file__))
from pathways import MODALITIES, source_ids  # noqa: E402
DESCENDING = {"descending", "motor"}
TOP_N = 50
TRAVERSAL_RUNS = 100
TRAVERSAL_STEPS = 12

METRICS = ["bw_weighted", "bw_unweighted", "influence", "current_flow",
           "traversal", "total_syn", "in_syn", "out_syn", "in_deg", "out_deg"]


def traversal_model(edges, seed_ids, all_ids, runs=TRAVERSAL_RUNS, steps=TRAVERSAL_STEPS, seed=0):
    """Probabilistic information-flow traversal (Schlegel/Costa style).

    Returns mean recruitment step per neuron; never-recruited -> steps+1.
    """
    rng = np.random.default_rng(seed)
    idx = {n: i for i, n in enumerate(all_ids)}
    n = len(all_ids)

    pre = edges["source"].map(idx).to_numpy()
    post = edges["target"].map(idx).to_numpy()
    w = edges["syn_count"].to_numpy(dtype=float)

    total_in = np.zeros(n)
    np.add.at(total_in, post, w)
    total_in[total_in == 0] = np.inf          # unreachable -> zero probability

    seed_mask0 = np.zeros(n, dtype=bool)
    seed_mask0[[idx[s] for s in seed_ids if s in idx]] = True

    acc = np.zeros(n)
    for r in range(runs):
        active = seed_mask0.copy()
        step_of = np.full(n, np.nan)
        step_of[active] = 0
        for s in range(1, steps + 1):
            inflow = np.zeros(n)
            live = active[pre]
            np.add.at(inflow, post[live], w[live])
            p = np.clip(inflow / total_in, 0, 1)
            newly = (~active) & (rng.random(n) < p)
            if not newly.any():
                break
            step_of[newly] = s
            active |= newly
        step_of[np.isnan(step_of)] = steps + 1
        acc += step_of
    return -(acc / runs)      # negate: higher = earlier = more important


def current_flow(edges, nodes, sources, targets):
    """Current-flow betweenness. Undirected only -- see module docstring."""
    G = nx.from_pandas_edgelist(edges, "source", "target", edge_attr="syn_count",
                                create_using=nx.Graph)
    G.add_nodes_from(nodes["root_id"])
    if G.number_of_nodes() == 0:
        return None
    G = G.subgraph(max(nx.connected_components(G), key=len)).copy()
    src = [s for s in sources if s in G]
    tgt = [t for t in targets if t in G]
    if not src or not tgt:
        return None
    cf = nx.current_flow_betweenness_centrality_subset(
        G, sources=src, targets=tgt, normalized=True, weight="syn_count")
    return cf


def overlap_vs_chance(df, a, b, k=TOP_N):
    """Top-k overlap between two metrics, with hypergeometric chance expectation."""
    d = df.dropna(subset=[a, b])
    N = len(d)
    if N < k * 2:
        return None
    sa = set(d.nlargest(k, a).index)
    sb = set(d.nlargest(k, b).index)
    obs = len(sa & sb)
    exp = k * k / N
    p = hypergeom.sf(obs - 1, N, k, k)
    return obs, exp, p, N


def main():
    import argparse, sys
    _ap = argparse.ArgumentParser(); _ap.add_argument('--modality', nargs='*', default=None)
    _a, _ = _ap.parse_known_args()
    mods = _a.modality or MODALITIES
    skip_cf = "--no-current-flow" in sys.argv
    lines = ["Metric agreement matrix", "=" * 70, ""]

    for m in mods:
        print(f"\n=== {m} ===", flush=True)
        edges = pd.read_csv(os.path.join(ROOT, f"subgraph_edges_{m}.csv"))
        nodes = pd.read_csv(os.path.join(ROOT, f"subgraph_nodes_{m}.csv"))

        df = nodes[["root_id", "super_class", "class"]].copy()
        for name, path in [("bw_weighted", f"ranked_{m}.csv"),
                           ("bw_unweighted", f"ranked_unweighted_{m}.csv")]:
            r = pd.read_csv(os.path.join(ROOT, path))[["root_id", "betweenness"]]
            df = df.merge(r.rename(columns={"betweenness": name}), on="root_id", how="left")

        infp = os.path.join(ROOT, f"influence_{m}.csv")
        if os.path.exists(infp):
            r = pd.read_csv(infp)[["root_id", "adjusted"]]
            df = df.merge(r.rename(columns={"adjusted": "influence"}), on="root_id", how="left")

        # --- trivial baselines ---
        gi = edges.groupby("target")["syn_count"].agg(["sum", "count"])
        go = edges.groupby("source")["syn_count"].agg(["sum", "count"])
        df["in_syn"] = df.root_id.map(gi["sum"]).fillna(0)
        df["in_deg"] = df.root_id.map(gi["count"]).fillna(0)
        df["out_syn"] = df.root_id.map(go["sum"]).fillna(0)
        df["out_deg"] = df.root_id.map(go["count"]).fillna(0)
        df["total_syn"] = df.in_syn + df.out_syn

        # --- traversal ---
        seeds = source_ids(nodes, m).tolist()
        print("  traversal model...", flush=True)
        df["traversal"] = traversal_model(edges, seeds, df.root_id.tolist())

        # --- current flow ---
        df["current_flow"] = np.nan
        if not skip_cf:
            tgts = nodes.loc[nodes.super_class.isin(DESCENDING), "root_id"].tolist()
            print(f"  current-flow (symmetrized, {len(nodes)} nodes)...", flush=True)
            try:
                cf = current_flow(edges, nodes, seeds, tgts)
                if cf:
                    df["current_flow"] = df.root_id.map(cf)
                    print("    ok", flush=True)
            except (MemoryError, Exception) as e:
                print(f"    SKIPPED: {type(e).__name__}: {str(e)[:70]}", flush=True)

        df.to_csv(os.path.join(ROOT, f"metric_matrix_{m}.csv"), index=False)

        # --- agreement, intermediaries only ---
        mid = df[(df.super_class == "central")].set_index("root_id")
        present = [c for c in METRICS if c in mid and mid[c].notna().sum() > TOP_N * 2]

        lines.append(f"--- {m}  (intermediary neurons: {len(mid)}) ---")
        lines.append("")
        lines.append("Spearman rho:")
        hdr = "  " + "".join(f"{c[:9]:>11s}" for c in present)
        lines.append(" " * 15 + hdr)
        for a in present:
            row = f"  {a:>13s}"
            for b in present:
                v = spearmanr(mid[a], mid[b], nan_policy="omit")[0]
                row += f"{v:>11.2f}"
            lines.append(row)
        lines.append("")
        lines.append(f"Top-{TOP_N} overlap vs chance  (obs / expected, p):")
        for i, a in enumerate(present):
            for b in present[i + 1:]:
                res = overlap_vs_chance(mid, a, b)
                if res:
                    obs, exp, p, N = res
                    flag = "" if p < 0.01 else "   <- indistinguishable from chance"
                    lines.append(f"  {a:>13s} vs {b:<13s} {obs:3d} / {exp:5.2f}   p={p:.1e}{flag}")
        lines.append("")
        print("\n".join(lines[-6:]), flush=True)

    out = "\n".join(lines)
    with open(os.path.join(ROOT, "metric_agreement.txt"), "w") as f:
        f.write(out + "\n")
    print("\nsaved metric_agreement.txt")


if __name__ == "__main__":
    main()
