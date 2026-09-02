#!/usr/bin/env python
"""
null_degree_preserving.py -- Null B. Is a top-50 neuron more of a bottleneck than
its own degree already implies?

Null A (null_weight_permutation.py) tested the WEIGHTING. This tests the NEURONS,
and it is the test the metric agreement matrix made urgent: weighted betweenness
overlaps raw synapse count at 23/50 (olfactory) and 26/50 (visual), so a high
betweenness score is not by itself evidence of anything beyond being well
connected.

NULL
  Directed double-edge swap: repeatedly take two edges u1->v1, u2->v2 and rewire
  them to u1->v2, u2->v1. This preserves every node's in-degree and out-degree
  exactly, and (because weights ride with the source slot) every node's total
  out-synapse count. What it destroys is which specific partners a neuron has --
  i.e. its position in the pathway. A neuron whose betweenness survives this is
  a bottleneck because of where it sits, not because of how many synapses it has.

METRIC
  Same weighted betweenness as Phase A/B (distance = 1/syn_count, restricted to
  sensory-source -> descending-target paths), but computed from a fixed sample of
  sources so that trials are affordable. The sample is identical across the real
  graph and every null trial, so scores are directly comparable; only the absolute
  scale differs from the full-source run in RESULTS.md.

READ
  Per neuron: z = (real - null_mean) / null_sd, plus an empirical one-sided p from
  the trial distribution. Reported for the top 50, since those are the neurons the
  study makes claims about.

CAVEAT -- selection bias (winner's curse)
  The top 50 are chosen by REAL betweenness and then tested against their own
  null; nodes chosen for being extreme sit above their null mean even in a graph
  with no positional structure. The survival count therefore has a nonzero
  false-positive floor. nullB_selection_control.py measures that floor by
  running this exact procedure on a shuffled graph treated as data; read the two
  together (RESULTS.md, "Null B selection-bias control").

Usage:  python3 null_degree_preserving.py [--trials N] [--sources N] [--modality M]
Output: null_degree_<modality>.csv, null_degree_<modality>.txt
"""
import argparse
import os
import time

import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT = os.path.dirname(os.path.abspath(__file__))
from pathways import MODALITIES, source_ids  # noqa: E402
DESCENDING = {"descending", "motor"}
TOP_N = 50
SWAP_FACTOR = 5          # attempted swaps = SWAP_FACTOR * n_edges
BATCH = 50_000


def benjamini_hochberg(p):
    """BH step-up FDR. 50 neurons are tested per modality; uncorrected p <= 0.05
    would expect ~2.5 false positives per pathway on its own."""
    p = np.asarray(p, dtype=float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order] * n / np.arange(1, n + 1)
    q_sorted = np.minimum.accumulate(ranked[::-1])[::-1]
    q = np.empty(n)
    q[order] = np.clip(q_sorted, 0, 1)
    return q


def double_edge_swap(src, dst, rng, factor=SWAP_FACTOR):
    """Directed double-edge swap preserving in- and out-degree of every node.

    Vectorized in batches: propose many swaps at once, reject any that would make
    a self-loop or a duplicate edge, apply the survivors. Weights are not touched
    (they stay attached to the source slot), so out-synapse totals are preserved.
    """
    src, dst = src.copy(), dst.copy()
    present = set(zip(src.tolist(), dst.tolist()))
    m = len(src)
    target = factor * m
    done = 0
    while done < target:
        k = min(BATCH, target - done)
        i = rng.integers(0, m, k)
        j = rng.integers(0, m, k)
        u1, v1, u2, v2 = src[i], dst[i], src[j], dst[j]
        ok = (i != j) & (u1 != v2) & (u2 != v1)
        for a, b, c, d, e, f in zip(i[ok], j[ok], u1[ok], v2[ok], u2[ok], v1[ok]):
            if (c, d) in present or (e, f) in present:
                continue
            present.discard((c, dst[a]))
            present.discard((e, dst[b]))
            dst[a], dst[b] = d, f
            present.add((c, d))
            present.add((e, f))
        done += k
    return src, dst


def betweenness(src, dst, w, nodes, sources, targets):
    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    G.add_weighted_edges_from(zip(src.tolist(), dst.tolist(), (1.0 / w).tolist()), weight="d")
    return nx.betweenness_centrality_subset(G, sources=sources, targets=targets,
                                            normalized=True, weight="d")


def run(modality, trials, n_sources, seed=0, root=None):
    root = root or ROOT
    rng = np.random.default_rng(seed)
    edges = pd.read_csv(os.path.join(root, f"subgraph_edges_{modality}.csv"))
    nodes_df = pd.read_csv(os.path.join(root, f"subgraph_nodes_{modality}.csv"))
    nodes = nodes_df.root_id.tolist()

    src = edges.source.to_numpy()
    dst = edges.target.to_numpy()
    w = edges.syn_count.to_numpy(dtype=float)

    pool = source_ids(nodes_df, modality).to_numpy()
    targets = nodes_df.loc[nodes_df.super_class.isin(DESCENDING), "root_id"].tolist()
    sources = sorted(rng.choice(pool, min(n_sources, len(pool)), replace=False).tolist())

    ranked = pd.read_csv(os.path.join(root, f"ranked_{modality}.csv"))
    top = ranked.head(TOP_N).root_id.tolist()

    print(f"[{modality}] {len(nodes)} nodes, {len(src)} edges, "
          f"{len(sources)} sampled sources, {len(targets)} targets, {trials} trials",
          flush=True)

    t0 = time.time()
    real = betweenness(src, dst, w, nodes, sources, targets)
    print(f"  real betweenness: {time.time() - t0:.0f}s", flush=True)

    null = np.zeros((trials, TOP_N))
    for t in range(trials):
        t1 = time.time()
        s2, d2 = double_edge_swap(src, dst, rng)
        bt = betweenness(s2, d2, w, nodes, sources, targets)
        null[t] = [bt.get(r, 0.0) for r in top]
        print(f"  trial {t + 1}/{trials}  {time.time() - t1:.0f}s", flush=True)

    real_v = np.array([real.get(r, 0.0) for r in top])
    mu, sd = null.mean(axis=0), null.std(axis=0, ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        z = np.where(sd > 0, (real_v - mu) / sd, np.inf)

    # Empirical p with the standard +1 correction: with `trials` shuffles the
    # smallest attainable p is 1/(trials+1), never 0 -- reporting p = 0 from a
    # finite permutation set overstates the evidence.
    p = ((null >= real_v).sum(axis=0) + 1) / (trials + 1)
    # Parametric complement: the empirical p is quantised at 1/(trials+1), which
    # is too coarse to survive multiple-comparison correction at small trial
    # counts. p_z assumes the null betweenness is roughly normal across shuffles.
    p_z = norm.sf(z)
    q = benjamini_hochberg(p)
    q_z = benjamini_hochberg(p_z)

    cpath = os.path.join(root, f"characterized_{modality}.csv")
    if os.path.exists(cpath):
        meta = pd.read_csv(cpath).set_index("root_id")[["primary_type", "neuropil"]]
    else:
        # replication dirs carry annotations rather than a characterized_ file
        apath = os.path.join(root, "mcns_annotations.csv")
        a_ = pd.read_csv(apath).set_index("root_id") if os.path.exists(apath) else None
        meta = pd.DataFrame({"primary_type": a_.primary_type if a_ is not None else [],
                             "neuropil": ""}) if a_ is not None else \
            pd.DataFrame(columns=["primary_type", "neuropil"])
        if a_ is not None:
            meta["neuropil"] = ""
    out = pd.DataFrame({
        "root_id": top,
        "rank": np.arange(1, TOP_N + 1),
        "primary_type": [meta.primary_type.get(r, "") for r in top],
        "neuropil": [meta.neuropil.get(r, "") for r in top],
        "real": real_v, "null_mean": mu, "null_sd": sd, "z": z,
        "p_emp": p, "q_emp": q, "p_z": p_z, "q_z": q_z,
    })
    out.to_csv(os.path.join(root, f"null_degree_{modality}.csv"), index=False)

    surv = int((out.p_emp <= 0.05).sum())
    surv_q = int((out.q_emp <= 0.05).sum())
    surv_qz = int((out.q_z <= 0.05).sum())
    top25_qz = int((out.q_z.head(25) <= 0.05).sum())
    zero = int((out.null_mean == 0).sum())
    lines = [
        f"Null B -- degree-preserving edge swap ({modality})",
        "=" * 60, "",
        f"graph            {len(nodes)} nodes, {len(src)} edges",
        f"sources          {len(sources)} sampled of {len(pool)} (seed {seed})",
        f"targets          {len(targets)}",
        f"trials           {trials}   ({SWAP_FACTOR}x|E| swap attempts each)",
        "",
        "Preserves every neuron's in-degree, out-degree and out-synapse total;",
        "destroys which partners it connects to. A neuron that keeps a high",
        "betweenness here is a bottleneck by position, not by connection count.",
        "",
        f"top-{TOP_N} above null, uncorrected p_emp<=0.05:  {surv}/{TOP_N}",
        f"top-{TOP_N} above null, BH-FDR q_emp<=0.05:       {surv_q}/{TOP_N}",
        f"top-{TOP_N} above null, BH-FDR q_z<=0.05:         {surv_qz}/{TOP_N}",
        f"top-25  above null, BH-FDR q_z<=0.05:         {top25_qz}/25",
        f"(empirical p floor is 1/(trials+1) = {1/(trials+1):.4f})",
        f"top-{TOP_N} neurons whose null betweenness is exactly 0:  {zero}/{TOP_N}",
        f"median z:  {np.median(out.z[np.isfinite(out.z)]):.2f}",
        "",
        f"{'rank':>4} {'cell type':<12}{'neuropil':<9}{'real':>11}{'null mean':>11}{'z':>8}{'q_z':>9}",
    ]
    for _, r in out.iterrows():
        zs = "inf" if not np.isfinite(r.z) else f"{r.z:.1f}"
        lines.append(f"{int(r['rank']):>4} {str(r.primary_type):<12}{str(r.neuropil):<9}"
                     f"{r.real:>11.3e}{r.null_mean:>11.3e}{zs:>8}{r.q_z:>9.1e}")
    txt = "\n".join(lines) + "\n"
    with open(os.path.join(root, f"null_degree_{modality}.txt"), "w") as f:
        f.write(txt)
    print(txt, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=20)
    ap.add_argument("--sources", type=int, default=100)
    ap.add_argument("--modality", default=None)
    ap.add_argument("--root", default=None)
    a = ap.parse_args()
    root = None
    if a.root:
        root = a.root if os.path.isabs(a.root) else os.path.join(ROOT, a.root)
    for m in ([a.modality] if a.modality else MODALITIES):
        run(m, a.trials, a.sources, root=root)


if __name__ == "__main__":
    main()
