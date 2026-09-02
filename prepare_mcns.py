#!/usr/bin/env python
"""
prepare_mcns.py -- build the same pathway subgraphs on a SECOND connectome.
NOTE: MCNS annotates no ocellar photoreceptors, so FAFB's "ocellar" pathway has
no MCNS counterpart. MCNS `class == visual` is compound-eye R1-R8 and is built
under the name "photoreceptor"; "visual" is the lamina/medulla input pathway
(see pathways.py). Source definitions: pathways.MCNS_SOURCE_DEFINITION.

Everything in this study so far rests on FAFB v783: one brain, one individual, one
sex. This replicates the graph construction on the Janelia male CNS (MCNS v0.9),
which differs on all three counts and additionally includes the ventral nerve
cord. Codex publishes a weighted connections export for it at the same base URL
as FAFB's, with an identical schema, so no new solver is needed.

WHY MCNS AND NOT BANC
  BANC also has a public weighted export, but its Class vocabulary names sensory
  cells '<modality>_receptor_neuron' and carries no mechanosensory class, so two
  of the three pathways would need hand-built label mappings. MCNS uses 'olfactory'
  / 'visual' / 'mechanosensory' directly. BANC remains the natural third dataset.

WHAT IS DIFFERENT, AND WHY IT MATTERS
  MCNS contains the VNC, so descending neurons are no longer the end of the line:
  720 real motor neurons are present. The pathway can therefore be run to actual
  effectors. Both endpoint definitions are built here:
    endpoint=descending   directly comparable to the FAFB results
    endpoint=motor        the biologically correct target, FAFB cannot do this
  Comparing the two on the same graph also measures how much the FAFB endpoint
  choice distorted the answer -- a limitation the study could previously only
  declare, not quantify.

LABEL MAPPING (MCNS -> the FAFB vocabulary the pipeline expects)
  super_class: descending_neuron -> descending, vnc_motor -> motor,
               *_sensory -> sensory, {cb,ol,vnc}_intrinsic -> central, else verbatim
  class:       mechanosensory_tactile / _proprioceptive / _tbc -> mechanosensory
               (FAFB does not subdivide mechanosensory; collapsing keeps the two
               datasets comparable rather than inflating MCNS's source count)

Output mirrors the FAFB file contract exactly, under mcns/:
  subgraph_edges_<modality>.csv, subgraph_nodes_<modality>.csv
so betweenness.py and everything downstream run unchanged with NC_ROOT=mcns.

Usage:  python3 prepare_mcns.py [--endpoint descending|motor] [--force]
"""
import argparse
import os
import urllib.request

import networkx as nx
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
META = os.path.join(ROOT, "data", "meta")
URL = "https://storage.googleapis.com/flywire-data/codex/data/mcns/0.9/connections_princeton.csv.gz"
CONN = os.path.join(META, "mcns_connections.csv.gz")
NEURONS = os.path.join(META, "mcns_neurons.csv.gz")
from pathways import MCNS_MODALITIES as MODALITIES, MCNS_SOURCE_DEFINITION, mcns_source_ids  # noqa: E402
MAX_HOPS = 2

SUPER_MAP = {"descending_neuron": "descending", "vnc_motor": "motor",
             "ascending_neuron": "ascending", "cb_intrinsic": "central",
             "ol_intrinsic": "optic", "vnc_intrinsic": "central",
             "cb_sensory": "sensory", "ol_sensory": "sensory",
             "vnc_sensory": "sensory"}
CLASS_MAP = {"mechanosensory_tactile": "mechanosensory",
             "mechanosensory_proprioceptive": "mechanosensory",
             "mechanosensory_tbc": "mechanosensory"}


def fetch():
    if os.path.exists(CONN):
        print(f"have   mcns_connections.csv.gz ({os.path.getsize(CONN)/1e6:.0f} MB)")
        return
    print(f"GET    {URL}")
    urllib.request.urlretrieve(URL, CONN)
    print(f"saved  ({os.path.getsize(CONN)/1e6:.0f} MB)")


def annotations():
    d = pd.read_csv(NEURONS, usecols=["Root ID", "Super Class", "Class", "Primary Cell Type"],
                    low_memory=False)
    d.columns = ["root_id", "super_class", "class", "primary_type"]
    d["super_class"] = d.super_class.map(lambda v: SUPER_MAP.get(v, v))
    d["class"] = d["class"].map(lambda v: CLASS_MAP.get(v, v))
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", choices=["descending", "motor"], default="descending")
    ap.add_argument("--modality", nargs="*", default=MODALITIES)
    a = ap.parse_args()
    endpoint_classes = {"descending": {"descending", "motor"}, "motor": {"motor"}}[a.endpoint]
    out_dir = os.path.join(ROOT, "mcns" if a.endpoint == "descending" else "mcns_motor")
    os.makedirs(out_dir, exist_ok=True)

    fetch()
    ann = annotations()
    print(f"annotations: {len(ann)} neurons")

    conn = pd.read_csv(CONN, usecols=["pre_root_id", "post_root_id", "syn_count"])
    print(f"  {len(conn)} (pre, post, neuropil) rows")
    edges = (conn.groupby(["pre_root_id", "post_root_id"], as_index=False, sort=False)
             ["syn_count"].sum())
    print(f"  {len(edges)} unique pairs, min syn_count {edges.syn_count.min()}")

    G = nx.from_pandas_edgelist(edges, "pre_root_id", "post_root_id",
                                edge_attr="syn_count", create_using=nx.DiGraph)
    G_rev = G.reverse(copy=False)
    print(f"  full graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    tgt_ids = set(ann.loc[ann.super_class.isin(endpoint_classes), "root_id"])
    tgt_in = [t for t in tgt_ids if t in G]
    print(f"  {a.endpoint} targets: {len(tgt_ids)} ({len(tgt_in)} in graph)")

    hop = lambda u, v, d: 1  # noqa: E731
    bwd = nx.multi_source_dijkstra_path_length(G_rev, tgt_in, weight=hop)
    can_reach = {n for n, d in bwd.items() if d <= MAX_HOPS} | tgt_ids

    label_map = ann.set_index("root_id")[["super_class", "class"]]

    for modality in a.modality:
        print(f"\n=== {modality} ({a.endpoint}) ===")
        print(f"  sources: {MCNS_SOURCE_DEFINITION[modality]}")
        sens = mcns_source_ids(modality, ann)
        sens_in = [s for s in sens if s in G]
        print(f"  sensory: {len(sens)} ({len(sens_in)} in graph)")
        fwd = nx.multi_source_dijkstra_path_length(G, sens_in, weight=hop)
        reach = {n for n, d in fwd.items() if d <= MAX_HOPS} | sens

        sub = G.subgraph(reach & can_reach).copy()
        print(f"  subgraph: {sub.number_of_nodes()} nodes, {sub.number_of_edges()} edges")

        nx.to_pandas_edgelist(sub).to_csv(
            os.path.join(out_dir, f"subgraph_edges_{modality}.csv"), index=False)
        nodes_out = pd.DataFrame({"root_id": list(sub.nodes())}).join(label_map, on="root_id")
        nodes_out["super_class"] = nodes_out["super_class"].fillna("unknown")
        nodes_out["class"] = nodes_out["class"].fillna("unknown")
        nodes_out["is_source"] = nodes_out["root_id"].isin(sens)
        nodes_out.to_csv(os.path.join(out_dir, f"subgraph_nodes_{modality}.csv"), index=False)
        n_src = int(nodes_out["is_source"].sum())
        n_tgt = int(nodes_out.super_class.isin(endpoint_classes).sum())
        print(f"  in subgraph: {n_src} sources, {n_tgt} {a.endpoint} targets")

    ann.to_csv(os.path.join(out_dir, "mcns_annotations.csv"), index=False)
    print(f"\nsaved to {out_dir}/")


if __name__ == "__main__":
    main()
