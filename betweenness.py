#!/usr/bin/env python
"""
betweenness.py -- rank neurons in each pathway subgraph by betweenness
centrality restricted to sensory-source -> descending-target paths
(Phase A/B, Project 7).

Weighted, per proposal section 4 Phase A step 3. Edge distance = 1 / syn_count,
so a heavily-connected pair (many synapses) is "shorter" -- i.e. a cheaper route
for information -- than a pair joined by a handful of synapses. Shortest paths
therefore prefer strong connections, and a neuron scores as a bottleneck only if
the *strong* routes run through it.

The synapse counts come from Codex's connections export (see
download_connections.py); an earlier version of this script ran unweighted
because the pair list then in use carried no counts.

Input (per modality, from build_pathway_subgraphs.py):
  subgraph_edges_<modality>.csv   (source, target, syn_count)
  subgraph_nodes_<modality>.csv

Output (per modality):
  ranked_<modality>.csv   root_id, betweenness, rank (all nodes, sorted)
"""
import os

import networkx as nx
import pandas as pd

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
from pathways import MODALITIES, source_ids  # noqa: E402
DESCENDING_CLASSES = {"descending", "motor"}


def main():
    import argparse
    import numpy as np
    ap = argparse.ArgumentParser()
    ap.add_argument("--modality", nargs="*", default=MODALITIES)
    ap.add_argument("--sample", type=int, default=None,
                    help="sample this many sources (seed 0) instead of exact all-source "
                         "betweenness; used for the lamina/medulla visual graph "
                         "(17k sources, 60k nodes) where exact is infeasible")
    a = ap.parse_args()
    for modality in a.modality:
        print(f"\n=== {modality} ===")
        edges = pd.read_csv(os.path.join(OUT_DIR, f"subgraph_edges_{modality}.csv"))
        nodes = pd.read_csv(os.path.join(OUT_DIR, f"subgraph_nodes_{modality}.csv"))
        print(f"  {len(nodes)} nodes, {len(edges)} edges")

        # Distance = 1/syn_count: strong (many-synapse) connections are short.
        edges["distance"] = 1.0 / edges["syn_count"]

        G = nx.from_pandas_edgelist(
            edges,
            source="source",
            target="target",
            edge_attr=["syn_count", "distance"],
            create_using=nx.DiGraph,
        )
        G.add_nodes_from(nodes["root_id"])

        sources = set(source_ids(nodes, modality)) & set(G)
        targets = set(nodes.loc[nodes["super_class"].isin(DESCENDING_CLASSES), "root_id"]) & set(G)
        print(f"  sources ({modality}): {len(sources)}, targets (descending): {len(targets)}")
        if a.sample and len(sources) > a.sample:
            rng = np.random.default_rng(0)
            sources = set(rng.choice(sorted(sources), a.sample, replace=False).tolist())
            print(f"  SAMPLED-SOURCE PROTOCOL: {len(sources)} sources (seed 0)")

        print(f"  computing betweenness_centrality_subset (weighted, {len(sources)} Dijkstra runs)...")
        bc = nx.betweenness_centrality_subset(
            G, sources=sources, targets=targets, normalized=True, weight="distance"
        )

        ranked = (
            pd.DataFrame({"root_id": list(bc.keys()), "betweenness": list(bc.values())})
            .sort_values("betweenness", ascending=False)
            .reset_index(drop=True)
        )
        ranked["rank"] = ranked.index + 1

        n_nonzero = (ranked["betweenness"] > 0).sum()
        print(f"  {n_nonzero} neurons with nonzero betweenness (on some shortest sensory->descending path)")
        print(ranked.head(10).to_string(index=False))

        out_path = os.path.join(OUT_DIR, f"ranked_{modality}.csv")
        ranked.to_csv(out_path, index=False)
        if a.sample and len(sources) == a.sample:
            with open(os.path.join(OUT_DIR, f"ranked_{modality}.PROTOCOL.txt"), "w") as fh:
                fh.write(f"sampled-source betweenness: {a.sample} sources, seed 0, "
                         f"{len(targets)} targets, all-target\n")
        print(f"  saved {out_path}")


if __name__ == "__main__":
    main()
