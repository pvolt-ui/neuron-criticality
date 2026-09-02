#!/usr/bin/env python
"""
generate_embeddings.py -- turn each neuron's connectivity pattern in the
sensory->descending subgraph into a fixed-length numeric embedding.

Method: connectivity-only spectral embedding (no cell-type labels used as input).
For each neuron we build two sparse vectors -- "who I send output to" (row of the
adjacency matrix) and "who sends input to me" (column of the adjacency matrix) --
and reduce each to a low-dimensional representation with truncated SVD (a fast,
deterministic stand-in for node2vec: neurons with similar input/output partner
patterns end up with similar embeddings). The two halves are concatenated into
one embedding per neuron.

Input:
  subgraph_edges.csv   from build_subgraph.py
  subgraph_nodes.csv   from build_subgraph.py

Output:
  embeddings.csv   one row per root_id, columns out_0..out_{K-1}, in_0..in_{K-1}
"""
import os

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
EDGES_PATH = os.path.join(OUT_DIR, "subgraph_edges.csv")
NODES_PATH = os.path.join(OUT_DIR, "subgraph_nodes.csv")

N_COMPONENTS = 32  # per direction -> 64-dim embedding total


def main():
    print("Loading subgraph...")
    edges = pd.read_csv(EDGES_PATH)
    nodes = pd.read_csv(NODES_PATH)
    node_ids = nodes["root_id"].tolist()
    n = len(node_ids)
    print(f"  {n} nodes, {len(edges)} edges")

    idx = {root_id: i for i, root_id in enumerate(node_ids)}
    rows = edges["source"].map(idx)
    cols = edges["target"].map(idx)
    valid = rows.notna() & cols.notna()
    rows = rows[valid].astype(int).to_numpy()
    cols = cols[valid].astype(int).to_numpy()
    data = np.ones(len(rows), dtype=np.float32)

    adj = csr_matrix((data, (rows, cols)), shape=(n, n))
    print(f"  adjacency matrix: {adj.shape}, {adj.nnz} nonzeros")

    print(f"Reducing outgoing-connectivity rows to {N_COMPONENTS} dims...")
    out_svd = TruncatedSVD(n_components=N_COMPONENTS, random_state=0)
    out_embed = out_svd.fit_transform(adj)
    print(f"  explained variance ratio (sum): {out_svd.explained_variance_ratio_.sum():.3f}")

    print(f"Reducing incoming-connectivity columns to {N_COMPONENTS} dims...")
    in_svd = TruncatedSVD(n_components=N_COMPONENTS, random_state=0)
    in_embed = in_svd.fit_transform(adj.transpose())
    print(f"  explained variance ratio (sum): {in_svd.explained_variance_ratio_.sum():.3f}")

    out_cols = [f"out_{i}" for i in range(N_COMPONENTS)]
    in_cols = [f"in_{i}" for i in range(N_COMPONENTS)]
    embed_df = pd.DataFrame(
        np.hstack([out_embed, in_embed]), columns=out_cols + in_cols
    )
    embed_df.insert(0, "root_id", node_ids)
    embed_df["super_class"] = nodes["super_class"].values

    out_path = os.path.join(OUT_DIR, "embeddings.csv")
    embed_df.to_csv(out_path, index=False)
    print(f"\nSaved {len(embed_df)} embeddings ({len(out_cols) + len(in_cols)}-dim) to {out_path}")


if __name__ == "__main__":
    main()
