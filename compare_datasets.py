#!/usr/bin/env python
"""
compare_datasets.py -- do the bottlenecks replicate in a second connectome?

Root IDs are dataset-specific, so nothing can be compared neuron by neuron. Cell
TYPES are the shared vocabulary, and they are also the level at which a
connectomics claim is normally made ("lLN2T_c is a bottleneck", not "neuron
720575940626612228 is").

WHAT IS COMPARED
  For each pathway, the top-N cell types by betweenness in FAFB v783 (female
  brain) against MCNS v0.9 (male CNS), both computed under the same sampled-source
  protocol (replicate_betweenness.py) so the protocol is not a confound.

  A neuron's betweenness is assigned to its cell type; a type's score is the MAX
  over its members, because a type is a bottleneck if any of its copies is, and
  copy counts differ between datasets.

CHANCE BASELINE
  Overlap counts mean nothing without one: the two datasets share only the types
  present in both, so the hypergeometric expectation is computed over that shared
  vocabulary and reported alongside every observed count.

Usage:  python3 compare_datasets.py [--top 25]
Output: dataset_comparison.csv, dataset_comparison.txt
"""
import argparse
import os

import numpy as np
import pandas as pd
from scipy.stats import hypergeom, spearmanr

ROOT = os.path.dirname(os.path.abspath(__file__))
META = os.path.join(ROOT, "data", "meta")
from pathways import MODALITIES, source_ids  # noqa: E402


def fafb_types():
    t = pd.read_csv(os.path.join(META, "fafb_consolidated_cell_types.csv.gz"))[
        ["root_id", "primary_type"]]
    return t.set_index("root_id").primary_type


def mcns_types():
    a = pd.read_csv(os.path.join(ROOT, "mcns", "mcns_annotations.csv"))
    return a.set_index("root_id").primary_type


def type_scores(ranked_path, tmap):
    """Max betweenness per cell type."""
    r = pd.read_csv(ranked_path)
    r["primary_type"] = r.root_id.map(tmap)
    r = r.dropna(subset=["primary_type"])
    r = r[r.primary_type.astype(str).str.strip() != ""]
    return r.groupby("primary_type").betweenness.max().sort_values(ascending=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=25)
    a = ap.parse_args()
    ft, mt = fafb_types(), mcns_types()
    rows, lines = [], ["Cross-dataset replication: FAFB v783 vs MCNS v0.9",
                       "=" * 66, "",
                       "Cell-type level, max betweenness per type, shared 150-source protocol.",
                       ""]

    for m in MODALITIES:
        fp = os.path.join(ROOT, f"ranked_{m}_sampled.csv")
        mp = os.path.join(ROOT, "mcns", f"ranked_{m}.csv")
        if not (os.path.exists(fp) and os.path.exists(mp)):
            lines.append(f"--- {m}: missing ranking, skipped ---\n")
            continue
        f, c = type_scores(fp, ft), type_scores(mp, mt)
        shared = sorted(set(f.index) & set(c.index))
        if len(shared) < a.top * 2:
            lines.append(f"--- {m}: only {len(shared)} shared cell types, too few ---\n")
            continue

        ftop = [t for t in f.index if t in set(shared)][:a.top]
        ctop = [t for t in c.index if t in set(shared)][:a.top]
        hit = sorted(set(ftop) & set(ctop))
        N, k = len(shared), a.top
        exp = k * k / N
        p = hypergeom.sf(len(hit) - 1, N, k, k)
        rho = spearmanr(f[shared].rank(ascending=False), c[shared].rank(ascending=False))[0]

        lines.append(f"--- {m} ---")
        lines.append(f"  cell types: FAFB {len(f)}, MCNS {len(c)}, shared {N}")
        lines.append(f"  top-{k} overlap: {len(hit)}   expected by chance {exp:.2f}   "
                     f"p = {p:.2e}")
        lines.append(f"  Spearman rho over all {N} shared types: {rho:+.3f}")
        if hit:
            lines.append(f"  replicating types: {', '.join(hit)}")
        lines.append("")
        for t in shared:
            rows.append(dict(modality=m, primary_type=t,
                             fafb_bw=f[t], mcns_bw=c[t],
                             fafb_rank=list(f.index).index(t) + 1,
                             mcns_rank=list(c.index).index(t) + 1,
                             in_both_top=t in set(hit)))

    if rows:
        pd.DataFrame(rows).to_csv(os.path.join(ROOT, "dataset_comparison.csv"), index=False)
    txt = "\n".join(lines) + "\n"
    with open(os.path.join(ROOT, "dataset_comparison.txt"), "w") as fh:
        fh.write(txt)
    print(txt)


if __name__ == "__main__":
    main()
