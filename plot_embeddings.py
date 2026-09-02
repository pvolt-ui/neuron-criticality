#!/usr/bin/env python
"""
plot_embeddings.py -- 2D visualization of the connectivity embeddings, colored by
super_class (sensory / descending / other), to show the embeddings visually separate
neurons by their role in the pathway.

Input:  embeddings.csv (from generate_embeddings.py)
Output: embedding_plot.png
"""
import os

import matplotlib.pyplot as plt
import pandas as pd
import umap

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
EMBEDDINGS_PATH = os.path.join(OUT_DIR, "embeddings.csv")


def main():
    print("Loading embeddings...")
    df = pd.read_csv(EMBEDDINGS_PATH)
    feature_cols = [c for c in df.columns if c.startswith("out_") or c.startswith("in_")]
    X = df[feature_cols].to_numpy()
    print(f"  {X.shape[0]} neurons, {X.shape[1]}-dim embeddings")

    print("Running UMAP to project to 2D...")
    reducer = umap.UMAP(n_components=2, random_state=0)
    coords = reducer.fit_transform(X)
    df["umap_x"] = coords[:, 0]
    df["umap_y"] = coords[:, 1]

    label_groups = {
        "sensory": ["sensory", "sensory_ascending"],
        "descending": ["descending", "motor"],
    }

    def group_label(sc):
        for group, members in label_groups.items():
            if sc in members:
                return group
        return "other"

    df["group"] = df["super_class"].apply(group_label)

    print("Plotting...")
    fig, ax = plt.subplots(figsize=(9, 7))
    colors = {"sensory": "#1f77b4", "descending": "#d62728", "other": "#cccccc"}
    for group, color in colors.items():
        subset = df[df["group"] == group]
        ax.scatter(
            subset["umap_x"], subset["umap_y"],
            s=6 if group == "other" else 14,
            c=color, label=f"{group} (n={len(subset)})",
            alpha=0.6 if group == "other" else 0.85,
            zorder=1 if group == "other" else 2,
        )
    ax.set_title("Connectivity Embeddings of the Sensory→Descending Subgraph (UMAP projection)")
    ax.set_xlabel("UMAP-1")
    ax.set_ylabel("UMAP-2")
    ax.legend()
    fig.tight_layout()

    out_path = os.path.join(OUT_DIR, "embedding_plot.png")
    fig.savefig(out_path, dpi=150)
    print(f"\nSaved plot to {out_path}")


if __name__ == "__main__":
    main()
