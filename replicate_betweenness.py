#!/usr/bin/env python
"""
replicate_betweenness.py -- weighted betweenness on any prepared subgraph
directory, under one protocol shared across datasets.

betweenness.py runs FAFB with every sensory source. MCNS is far larger (the
mechanosensory subgraph is 52k nodes / 2.5M edges against FAFB's 13.5k / 373k),
so exact all-source betweenness is not affordable there. Rather than compare a
full-source FAFB ranking against a sampled MCNS one -- which would confound the
dataset difference with the protocol difference -- this script runs BOTH datasets
with the same sampled-source protocol. The FAFB numbers it produces are therefore
not identical to ranked_<modality>.csv, and are meant only for the cross-dataset
comparison.

Usage:
  python3 replicate_betweenness.py --root mcns  [--sources 150] [--modality M]
  python3 replicate_betweenness.py --root .     --suffix _sampled
Output: <root>/ranked_<modality><suffix>.csv
"""
import argparse
import os
import time

import networkx as nx
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
from pathways import MODALITIES, source_ids  # noqa: E402
DESCENDING = {"descending", "motor"}
SEED = 0


def run(root, modality, n_sources, suffix):
    ep = os.path.join(root, f"subgraph_edges_{modality}.csv")
    if not os.path.exists(ep):
        print(f"[{modality}] missing {ep}, skipping")
        return
    edges = pd.read_csv(ep)
    nodes = pd.read_csv(os.path.join(root, f"subgraph_nodes_{modality}.csv"))

    src_pool = source_ids(nodes, modality).to_numpy()
    targets = nodes.loc[nodes.super_class.isin(DESCENDING), "root_id"].tolist()
    if len(src_pool) == 0 or not targets:
        print(f"[{modality}] no sources or targets, skipping")
        return

    rng = np.random.default_rng(SEED)
    sources = sorted(rng.choice(src_pool, min(n_sources, len(src_pool)),
                                replace=False).tolist())

    G = nx.DiGraph()
    G.add_nodes_from(nodes.root_id)
    G.add_weighted_edges_from(
        zip(edges.source, edges.target, 1.0 / edges.syn_count.astype(float)), weight="d")

    print(f"[{modality}] {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, "
          f"{len(sources)}/{len(src_pool)} sources, {len(targets)} targets", flush=True)
    t0 = time.time()
    bc = nx.betweenness_centrality_subset(G, sources=sources, targets=targets,
                                          normalized=True, weight="d")
    print(f"  done in {time.time() - t0:.0f}s", flush=True)

    out = (pd.DataFrame({"root_id": list(bc), "betweenness": list(bc.values())})
           .sort_values("betweenness", ascending=False, ignore_index=True))
    out["rank"] = np.arange(1, len(out) + 1)
    path = os.path.join(root, f"ranked_{modality}{suffix}.csv")
    out.to_csv(path, index=False)
    print(f"  saved {path}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="mcns")
    ap.add_argument("--sources", type=int, default=150)
    ap.add_argument("--suffix", default="")
    ap.add_argument("--modality", default=None)
    a = ap.parse_args()
    root = a.root if os.path.isabs(a.root) else os.path.join(HERE, a.root)
    for m in ([a.modality] if a.modality else MODALITIES):
        run(root, m, a.sources, a.suffix)


if __name__ == "__main__":
    main()
