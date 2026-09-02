#!/usr/bin/env python
"""
characterize.py -- join the top bottleneck neurons of each modality to
annotation data (cell type, neuropil, neurotransmitter, sub-class/nerve) and
plot what they are (Phase A/B write-up step, Project 7).

Neuropil now included. FAFB's per-neuron metadata tables genuinely have no
neuropil column -- an earlier version of this script stopped there and used
sub_class/nerve as an anatomical stand-in -- but the neuropil is recoverable
per-connection from Codex's connections export. See neuropil.py.

Input (per modality):
  ranked_<modality>.csv          from betweenness.py
Also reads:
  neuron_neuropil.csv                                root_id -> neuropil (via neuropil.py)
  ../data/meta/fafb_consolidated_cell_types.csv.gz   root_id -> primary_type
  ../data/meta/fafb_neurons.csv.gz                   root_id -> nt_type
  ../data/meta/fafb_classification.csv.gz            root_id -> sub_class, nerve

Output (per modality):
  characterized_<modality>.csv
  figure_top_celltypes_<modality>.png
  figure_top_neuropils_<modality>.png
"""
import os

import matplotlib.pyplot as plt
import pandas as pd

import neuropil

ROOT = os.path.dirname(os.path.abspath(__file__))
META = os.path.join(ROOT, "data", "meta")
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

from pathways import MODALITIES, source_ids  # noqa: E402
TOP_N = 50


def bar_figure(top, column, filename, title, color):
    """Horizontal bar chart of the most common values of `column` in the top-N."""
    counts = top[column].value_counts().head(15)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh(counts.index[::-1], counts.values[::-1], color=color)
    ax.set_xlabel(f"count in top-{TOP_N} betweenness-ranked neurons")
    ax.set_title(title)
    fig.tight_layout()
    path = os.path.join(OUT_DIR, filename)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  saved {path}")


def main():
    import argparse, sys
    _ap = argparse.ArgumentParser(); _ap.add_argument('--modality', nargs='*', default=None)
    _a, _ = _ap.parse_known_args()
    mods = _a.modality or MODALITIES
    npil = neuropil.build()[["root_id", "neuropil", "neuropil_frac"]]
    cell_types = pd.read_csv(os.path.join(META, "fafb_consolidated_cell_types.csv.gz"))[
        ["root_id", "primary_type"]
    ]
    neurons = pd.read_csv(os.path.join(META, "fafb_neurons.csv.gz"))[["root_id", "nt_type"]]
    classification = pd.read_csv(os.path.join(META, "fafb_classification.csv.gz"))[
        ["root_id", "super_class", "class", "sub_class", "nerve"]
    ]

    for modality in mods:
        print(f"\n=== {modality} ===")
        ranked = pd.read_csv(os.path.join(OUT_DIR, f"ranked_{modality}.csv"))
        top = ranked.head(TOP_N).copy()

        top = top.merge(cell_types, on="root_id", how="left")
        top = top.merge(neurons, on="root_id", how="left")
        top = top.merge(classification, on="root_id", how="left")
        top = top.merge(npil, on="root_id", how="left")

        top["primary_type"] = top["primary_type"].fillna("unknown")
        top["nt_type"] = top["nt_type"].fillna("unknown")
        top["neuropil"] = top["neuropil"].fillna("unknown")

        print(f"  top-{TOP_N} bottleneck cell types:")
        print(top["primary_type"].value_counts().head(10).to_string())
        print(f"  top-{TOP_N} bottleneck neuropils:")
        print(top["neuropil"].value_counts().head(10).to_string())
        print(f"  median neuropil dominance: {top['neuropil_frac'].median():.2f}")
        print(f"  top-{TOP_N} bottleneck neurotransmitters:")
        print(top["nt_type"].value_counts().to_string())

        out_csv = os.path.join(OUT_DIR, f"characterized_{modality}.csv")
        top.to_csv(out_csv, index=False)
        print(f"  saved {out_csv}")

        bar_figure(top, "primary_type", f"figure_top_celltypes_{modality}.png",
                   f"{modality}: top cell types among bottleneck neurons", "#1f77b4")
        bar_figure(top, "neuropil", f"figure_top_neuropils_{modality}.png",
                   f"{modality}: top neuropils among bottleneck neurons", "#d62728")


if __name__ == "__main__":
    main()
