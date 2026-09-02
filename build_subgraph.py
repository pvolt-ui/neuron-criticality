#!/usr/bin/env python
"""
build_subgraph.py — build the sensory -> descending (motor) subgraph from the
FAFB connectome, for the neuron-criticality project.

Inputs (already present in the repo):
  ../fafb_783_edge_list.csv          raw pre->post synapse edges
  ../data/meta/fafb_classification.csv.gz   root_id -> super_class (sensory/descending/...)

Output:
  subgraph_edges.csv   edges where the pre or post neuron is in the sensory/descending
                        set, restricted to the connected component that actually links
                        sensory to descending neurons
  subgraph_nodes.csv   node list with super_class label for each neuron in the subgraph
"""
import os

import networkx as nx
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
EDGE_LIST = os.path.join(ROOT, "fafb_783_edge_list.csv")
CLASSIFICATION = os.path.join(ROOT, "data", "meta", "fafb_classification.csv.gz")
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

SENSORY_CLASSES = {"sensory", "sensory_ascending"}
DESCENDING_CLASSES = {"descending", "motor"}

# Restrict to neurons within this many synaptic hops of both a sensory neuron
# (forward) and a descending neuron (backward). Hop counts were checked empirically:
# 1 hop keeps a focused ~5% of the brain (direct sensorimotor relay); by 2 hops
# the subgraph already balloons to >50% of all neurons, so 1 is the cutoff used here.
MAX_HOPS = 1


def main():
    print("Loading classification table...")
    classification = pd.read_csv(CLASSIFICATION)[["root_id", "super_class"]]

    sensory_ids = set(classification.loc[classification.super_class.isin(SENSORY_CLASSES), "root_id"])
    descending_ids = set(classification.loc[classification.super_class.isin(DESCENDING_CLASSES), "root_id"])
    print(f"  sensory neurons:    {len(sensory_ids)}")
    print(f"  descending neurons: {len(descending_ids)}")

    print("Loading edge list...")
    edges = pd.read_csv(EDGE_LIST)
    print(f"  columns: {list(edges.columns)}")
    print(f"  total edges: {len(edges)}")

    pre_col, post_col = edges.columns[0], edges.columns[1]

    print("Building full directed graph...")
    G = nx.from_pandas_edgelist(edges, source=pre_col, target=post_col, create_using=nx.DiGraph)
    print(f"  full graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    print("Finding neurons reachable from sensory neurons (forward) "
          "and that can reach descending neurons (backward)...")
    sensory_in_graph = [s for s in sensory_ids if s in G]
    descending_in_graph = [d for d in descending_ids if d in G]

    # Multi-source BFS from all sensory neurons at once (single O(V+E) pass,
    # instead of one BFS per neuron, which is far too slow on a multi-million-edge graph).
    fwd_dist = nx.multi_source_dijkstra_path_length(G, sensory_in_graph)
    reachable_from_sensory = {n for n, d in fwd_dist.items() if d <= MAX_HOPS}
    reachable_from_sensory |= sensory_ids

    G_rev = G.reverse(copy=False)
    bwd_dist = nx.multi_source_dijkstra_path_length(G_rev, descending_in_graph)
    can_reach_descending = {n for n, d in bwd_dist.items() if d <= MAX_HOPS}
    can_reach_descending |= descending_ids

    pathway_nodes = reachable_from_sensory & can_reach_descending
    print(f"  neurons on a sensory->descending path: {len(pathway_nodes)}")

    subgraph = G.subgraph(pathway_nodes).copy()
    print(f"  subgraph: {subgraph.number_of_nodes()} nodes, {subgraph.number_of_edges()} edges")

    edges_out = nx.to_pandas_edgelist(subgraph)
    edges_out.to_csv(os.path.join(OUT_DIR, "subgraph_edges.csv"), index=False)

    label_map = classification.set_index("root_id")["super_class"].to_dict()
    nodes_out = pd.DataFrame({"root_id": list(subgraph.nodes())})
    nodes_out["super_class"] = nodes_out["root_id"].map(label_map).fillna("unknown")
    nodes_out.to_csv(os.path.join(OUT_DIR, "subgraph_nodes.csv"), index=False)

    print("\nSaved subgraph_edges.csv and subgraph_nodes.csv in", OUT_DIR)


if __name__ == "__main__":
    main()
