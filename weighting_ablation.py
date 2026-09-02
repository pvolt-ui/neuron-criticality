#!/usr/bin/env python
"""
weighting_ablation.py -- attribute the change in bottleneck rankings to its two
causes.

Moving to Codex's connections export changed two things at once:
  (1) the graph itself -- the export is thresholded at >=5 synapses per pair,
      replacing an unthresholded pair list of unclear provenance;
  (2) the metric -- betweenness is now weighted by 1/syn_count rather than
      treating every connection as equal.

Comparing the final result against the old one therefore cannot say which cause
did the work. This script runs the *unweighted* metric on the *new* graph, which
sits between the two, so the change decomposes:

    old(unweighted, old graph)  ->  mid(unweighted, new graph)   = data effect
    mid(unweighted, new graph)  ->  new(weighted,   new graph)   = weighting effect

Input:  subgraph_edges_<modality>.csv, subgraph_nodes_<modality>.csv
        ranked_<modality>.csv                (weighted, current)
Output: ranked_unweighted_<modality>.csv     (the "mid" condition)
        weighting_ablation.txt
"""
import os

import networkx as nx
import pandas as pd

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
from pathways import MODALITIES, source_ids  # noqa: E402
DESCENDING_CLASSES = {"descending", "motor"}
TOP_N = 50


def unweighted_ranking(modality):
    edges = pd.read_csv(os.path.join(OUT_DIR, f"subgraph_edges_{modality}.csv"))
    nodes = pd.read_csv(os.path.join(OUT_DIR, f"subgraph_nodes_{modality}.csv"))

    G = nx.from_pandas_edgelist(edges, source="source", target="target", create_using=nx.DiGraph)
    G.add_nodes_from(nodes["root_id"])

    sources = set(source_ids(nodes, modality)) & set(G)
    targets = set(nodes.loc[nodes["super_class"].isin(DESCENDING_CLASSES), "root_id"]) & set(G)

    bc = nx.betweenness_centrality_subset(G, sources=sources, targets=targets, normalized=True)
    ranked = (
        pd.DataFrame({"root_id": list(bc.keys()), "betweenness": list(bc.values())})
        .sort_values("betweenness", ascending=False)
        .reset_index(drop=True)
    )
    ranked["rank"] = ranked.index + 1
    ranked.to_csv(os.path.join(OUT_DIR, f"ranked_unweighted_{modality}.csv"), index=False)
    return ranked


def main():
    import argparse, sys
    _ap = argparse.ArgumentParser(); _ap.add_argument('--modality', nargs='*', default=None)
    _a, _ = _ap.parse_known_args()
    mods = _a.modality or MODALITIES
    lines = ["Weighting vs data-change ablation (top-50 overlap)", "=" * 52, ""]
    for modality in mods:
        print(f"=== {modality} ===")
        mid = unweighted_ranking(modality)
        new = pd.read_csv(os.path.join(OUT_DIR, f"ranked_{modality}.csv"))

        mid50 = set(mid.head(TOP_N)["root_id"])
        new50 = set(new.head(TOP_N)["root_id"])
        overlap = len(mid50 & new50)

        lines.append(f"{modality}:")
        lines.append(f"  unweighted vs weighted, both on new graph: {overlap}/{TOP_N} shared")
        lines.append(f"  -> weighting alone changes {TOP_N - overlap}/{TOP_N} of the top-50")
        lines.append("")
        print(f"  weighting effect: {overlap}/{TOP_N} shared")

    summary = "\n".join(lines)
    with open(os.path.join(OUT_DIR, "weighting_ablation.txt"), "w") as f:
        f.write(summary + "\n")
    print("\n" + summary)


if __name__ == "__main__":
    main()
