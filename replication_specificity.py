#!/usr/bin/env python
"""
replication_specificity.py -- is cross-dataset replication specific to
betweenness, or would any degree-like ranking replicate as well?

Two sharpenings of compare_datasets.py:
  (1) Spearman rho restricted to cell types with NONZERO betweenness in both
      datasets (the all-types rho is inflated by the many types at exactly 0).
  (2) The same top-25 overlap / rho computed for a trivial baseline -- total
      synapse count per neuron (in + out, within the pathway subgraph), max per
      type -- under the identical shared-vocabulary hypergeometric test.
If betweenness replicates no better than total_syn, replication is evidence
that the PATHWAY is conserved, not that the betweenness ranking carries
conserved information beyond degree.
Output: replication_specificity.txt
"""
import os
import numpy as np
import pandas as pd
from scipy.stats import hypergeom, spearmanr

ROOT = os.path.dirname(os.path.abspath(__file__))
META = os.path.join(ROOT, "data", "meta")
TOP = 25


def type_map_fafb():
    return pd.read_csv(os.path.join(META, "fafb_consolidated_cell_types.csv.gz"))[
        ["root_id", "primary_type"]].set_index("root_id").primary_type


def type_map_mcns():
    return pd.read_csv(os.path.join(ROOT, "mcns", "mcns_annotations.csv")).set_index(
        "root_id").primary_type


def per_type(series, tmap):
    df = pd.DataFrame({"v": series})
    df["t"] = df.index.map(tmap)
    df = df.dropna(subset=["t"])
    df = df[df.t.astype(str).str.strip() != ""]
    return df.groupby("t").v.max()


def total_syn(root, m):
    e = pd.read_csv(os.path.join(root, f"subgraph_edges_{m}.csv"))
    s = e.groupby("source").syn_count.sum().add(e.groupby("target").syn_count.sum(), fill_value=0)
    return s


def test(f, c, label):
    shared = sorted(set(f.index) & set(c.index))
    f, c = f[shared], c[shared]
    ftop = set(f.sort_values(ascending=False).index[:TOP])
    ctop = set(c.sort_values(ascending=False).index[:TOP])
    hit = len(ftop & ctop)
    N = len(shared)
    p = hypergeom.sf(hit - 1, N, TOP, TOP)
    rho_all = spearmanr(f, c)[0]
    nz = (f > 0) & (c > 0)
    rho_nz = spearmanr(f[nz], c[nz])[0] if nz.sum() > 10 else float("nan")
    return (f"  {label:<22} shared {N:5d}  top-{TOP} overlap {hit:2d} (exp {TOP*TOP/N:.2f}, p={p:.1e})  "
            f"rho all {rho_all:+.3f}   rho nonzero-in-both (n={int(nz.sum())}) {rho_nz:+.3f}")


def main():
    ft, mt = type_map_fafb(), type_map_mcns()
    lines = ["Replication specificity: betweenness vs total-synapse baseline, FAFB vs MCNS",
             "=" * 90, ""]
    for m in ["olfactory", "mechanosensory", "visual"]:
        fp = os.path.join(ROOT, f"ranked_{m}_sampled.csv")
        mp = os.path.join(ROOT, "mcns", f"ranked_{m}.csv")
        if not (os.path.exists(fp) and os.path.exists(mp)):
            continue
        fb = per_type(pd.read_csv(fp).set_index("root_id").betweenness, ft)
        mb = per_type(pd.read_csv(mp).set_index("root_id").betweenness, mt)
        fs = per_type(total_syn(ROOT, m), ft)
        ms = per_type(total_syn(os.path.join(ROOT, "mcns"), m), mt)
        lines.append(f"--- {m} ---")
        lines.append(test(fb, mb, "betweenness"))
        lines.append(test(fs, ms, "total_syn baseline"))
        lines.append("")
    txt = "\n".join(lines) + "\n"
    open(os.path.join(ROOT, "replication_specificity.txt"), "w").write(txt)
    print(txt)


if __name__ == "__main__":
    main()
