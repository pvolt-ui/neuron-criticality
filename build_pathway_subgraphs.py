#!/usr/bin/env python
"""
build_pathway_subgraphs.py -- build one sensory -> descending (motor) subgraph
per sensory modality (olfactory, mechanosensory, visual, ocellar), for Phase A/B of the
neuron-criticality project (Project 7).

Weighted. Reads Codex's FAFB v783 connections export, which carries a synapse
count per (pre, post, neuropil) row; we sum those rows to one syn_count per
(pre, post) pair and carry it through as the edge weight. This replaces the old
`fafb_783_edge_list.csv`, a bare pair list inherited from an earlier project
that had no synapse counts (see download_connections.py).

SYNAPSE THRESHOLD: Codex's connections.csv is thresholded at >=5 synapses per
(pre, post) pair. Stating it explicitly because the threshold materially defines
the graph: 2,700,513 pairs here vs 3,732,460 in the old unthresholded pair list.

Inputs:
  ../data/meta/fafb_connections.csv.gz      pre, post, neuropil, syn_count, nt_type
  ../data/meta/fafb_classification.csv.gz   root_id -> super_class / class

Output, per modality in MODALITIES:
  subgraph_edges_<modality>.csv   (source, target, syn_count)
  subgraph_nodes_<modality>.csv   (root_id, super_class, class, is_source)

Cutoff: MAX_HOPS = 2 each way (a node is kept if it is within 2 synapses of a
source AND within 2 synapses of a descending neuron). See the MAX_HOPS comment.

Source definitions live in pathways.py. The pathway formerly called "visual"
(class == visual, i.e. photoreceptors) is now "ocellar": 142 of its 146
surviving sources were ocellar photoreceptors. "visual" is now the
lamina/medulla columnar input neurons (Lamina Monopolar, Transmedullary,
Medulla Intrinsic families), per the project spec. Node files carry an
`is_source` column; downstream scripts use pathways.source_mask().
"""
import os

import argparse

import networkx as nx
import pandas as pd

from pathways import MODALITIES, DESCENDING_CLASSES, fafb_source_ids, SOURCE_DEFINITION

ROOT = os.path.dirname(os.path.abspath(__file__))
CONNECTIONS = os.path.join(ROOT, "data", "meta", "fafb_connections.csv.gz")
CLASSIFICATION = os.path.join(ROOT, "data", "meta", "fafb_classification.csv.gz")
VISUAL_TYPES = os.path.join(ROOT, "data", "meta", "fafb_visual_neuron_types.csv.gz")
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# 1 hop each way leaves too few real endpoint neurons in the olfactory/visual
# subgraphs (checked live: 4 olfactory sources, 2 visual targets survive the
# intersection) -- the pathway from a photoreceptor or ORN to a descending
# neuron is multi-synaptic, so 1 hop each side barely overlaps. 2 hops keeps
# a solid fraction of real sensory/descending endpoints (olfactory: 2216/126,
# visual: 481/163) while staying betweenness-feasible (tens of thousands of
# nodes, not hundreds of thousands).
MAX_HOPS = 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modality", nargs="*", default=MODALITIES)
    args = ap.parse_args()

    print("Loading classification table...")
    classification = pd.read_csv(CLASSIFICATION)[["root_id", "super_class", "class", "sub_class"]]
    visual_types = pd.read_csv(VISUAL_TYPES)[["root_id", "family"]]

    print("Loading connections (pre, post, neuropil, syn_count)...")
    conn = pd.read_csv(CONNECTIONS, usecols=["pre_root_id", "post_root_id", "syn_count"])
    print(f"  {len(conn)} (pre, post, neuropil) rows")

    # One row per (pre, post): sum the per-neuropil synapse counts.
    edges = (
        conn.groupby(["pre_root_id", "post_root_id"], as_index=False, sort=False)["syn_count"]
        .sum()
    )
    print(f"  {len(edges)} unique (pre, post) pairs, min syn_count {edges.syn_count.min()}")

    print("Building full directed graph...")
    G = nx.from_pandas_edgelist(
        edges,
        source="pre_root_id",
        target="post_root_id",
        edge_attr="syn_count",
        create_using=nx.DiGraph,
    )
    G_rev = G.reverse(copy=False)
    print(f"  full graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    descending_ids = set(classification.loc[classification.super_class.isin(DESCENDING_CLASSES), "root_id"])
    descending_in_graph = [d for d in descending_ids if d in G]
    print(f"  descending neurons: {len(descending_ids)} ({len(descending_in_graph)} in graph)")

    # NOTE: the MAX_HOPS cutoff is deliberately *topological* -- 2 synapses, not
    # 2 units of weighted distance -- so hop counting forces every edge to 1
    # regardless of syn_count. Only betweenness.py uses the synapse weights.
    hop = lambda u, v, d: 1  # noqa: E731

    print("Backward BFS from descending neurons (shared across all modalities)...")
    bwd_dist = nx.multi_source_dijkstra_path_length(G_rev, descending_in_graph, weight=hop)
    can_reach_descending = {n for n, d in bwd_dist.items() if d <= MAX_HOPS}
    can_reach_descending |= descending_ids

    label_map = classification.set_index("root_id")[["super_class", "class"]]

    for modality in args.modality:
        print(f"\n=== {modality} ===")
        print(f"  sources: {SOURCE_DEFINITION[modality]}")
        sensory_ids = fafb_source_ids(modality, classification, visual_types)
        sensory_in_graph = [s for s in sensory_ids if s in G]
        print(f"  sensory neurons ({modality}): {len(sensory_ids)} ({len(sensory_in_graph)} in graph)")

        fwd_dist = nx.multi_source_dijkstra_path_length(G, sensory_in_graph, weight=hop)
        reachable_from_sensory = {n for n, d in fwd_dist.items() if d <= MAX_HOPS}
        reachable_from_sensory |= sensory_ids

        pathway_nodes = reachable_from_sensory & can_reach_descending
        print(f"  neurons on a {modality}->descending path: {len(pathway_nodes)}")

        subgraph = G.subgraph(pathway_nodes).copy()
        print(f"  subgraph: {subgraph.number_of_nodes()} nodes, {subgraph.number_of_edges()} edges")

        edges_out = nx.to_pandas_edgelist(subgraph)
        edges_out.to_csv(os.path.join(OUT_DIR, f"subgraph_edges_{modality}.csv"), index=False)

        nodes_out = pd.DataFrame({"root_id": list(subgraph.nodes())})
        nodes_out = nodes_out.join(label_map, on="root_id")
        nodes_out["super_class"] = nodes_out["super_class"].fillna("unknown")
        nodes_out["class"] = nodes_out["class"].fillna("unknown")
        nodes_out["is_source"] = nodes_out["root_id"].isin(sensory_ids)
        print(f"  sources in subgraph: {int(nodes_out.is_source.sum())}, "
              f"descending targets: {int(nodes_out.super_class.isin(DESCENDING_CLASSES).sum())}")
        nodes_out.to_csv(os.path.join(OUT_DIR, f"subgraph_nodes_{modality}.csv"), index=False)

        print(f"  saved subgraph_edges_{modality}.csv and subgraph_nodes_{modality}.csv")


if __name__ == "__main__":
    main()
