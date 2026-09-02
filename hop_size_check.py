#!/usr/bin/env python
"""
hop_size_check.py -- report subgraph size at different hop-distance limits,
to pick a reasonable cutoff for the sensory->descending subgraph.
"""
import os

import networkx as nx
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
EDGE_LIST = os.path.join(ROOT, "fafb_783_edge_list.csv")
CLASSIFICATION = os.path.join(ROOT, "data", "meta", "fafb_classification.csv.gz")

SENSORY_CLASSES = {"sensory", "sensory_ascending"}
DESCENDING_CLASSES = {"descending", "motor"}


def main():
    classification = pd.read_csv(CLASSIFICATION)[["root_id", "super_class"]]
    sensory_ids = set(classification.loc[classification.super_class.isin(SENSORY_CLASSES), "root_id"])
    descending_ids = set(classification.loc[classification.super_class.isin(DESCENDING_CLASSES), "root_id"])

    edges = pd.read_csv(EDGE_LIST)
    pre_col, post_col = edges.columns[0], edges.columns[1]
    G = nx.from_pandas_edgelist(edges, source=pre_col, target=post_col, create_using=nx.DiGraph)
    G_rev = G.reverse(copy=False)

    sensory_in_graph = [s for s in sensory_ids if s in G]
    descending_in_graph = [d for d in descending_ids if d in G]

    fwd_dist = nx.multi_source_dijkstra_path_length(G, sensory_in_graph)
    bwd_dist = nx.multi_source_dijkstra_path_length(G_rev, descending_in_graph)

    print(f"{'hops each way':>15} {'nodes in subgraph':>20} {'% of full graph':>18}")
    total_nodes = G.number_of_nodes()
    for hops in [1, 2, 3, 4, 5, 999]:
        within_fwd = {n for n, d in fwd_dist.items() if d <= hops}
        within_bwd = {n for n, d in bwd_dist.items() if d <= hops}
        pathway_nodes = within_fwd & within_bwd
        label = "unlimited" if hops == 999 else hops
        pct = 100 * len(pathway_nodes) / total_nodes
        print(f"{label:>15} {len(pathway_nodes):>20} {pct:>17.1f}%")


if __name__ == "__main__":
    main()
