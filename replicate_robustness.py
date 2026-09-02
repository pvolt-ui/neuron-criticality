#!/usr/bin/env python
"""
replicate_robustness.py -- does the redundancy result hold in a second connectome?

compare_datasets.py showed the RANKING replicates (rho 0.45-0.71 at cell-type
level). It says nothing about the other half of the study: that deleting a
bottleneck barely hurts, and that a handful of low-ranked neurons sever whole
sensory sources while the top-ranked ones do not. Those claims still rest on FAFB
alone. This runs the same deletion test on any prepared subgraph directory.

Same solver and the same endpoint-safe scoring as cross_modal_audit.py: damage is
measured only over source->target pairs whose own endpoints survive the deletion,
because deleting a neuron that is itself a source or target trivially kills its
own pairs.

Bands: top-50 by betweenness, ranks 1000-2000, and a size-matched random draw from
the whole graph for scale.

Usage:  python3 replicate_robustness.py [--root mcns] [--sources 100] [--n 15]
Output: <root>/robustness.csv, <root>/robustness.txt
"""
import argparse
import os

import numpy as np
import pandas as pd

from celltype_ablation import damage, solve

HERE = os.path.dirname(os.path.abspath(__file__))
from pathways import MODALITIES, source_ids  # noqa: E402
DESCENDING = {"descending", "motor"}
SEED = 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="mcns")
    ap.add_argument("--sources", type=int, default=100)
    ap.add_argument("--n", type=int, default=15, help="neurons tested per band")
    ap.add_argument("--ranked-suffix", default="")
    a = ap.parse_args()
    root = a.root if os.path.isabs(a.root) else os.path.join(HERE, a.root)

    rng = np.random.default_rng(SEED)
    rows, lines = [], [f"Robustness replication -- {os.path.basename(root) or 'fafb'}",
                       "=" * 62, ""]

    for m in MODALITIES:
        ep = os.path.join(root, f"subgraph_edges_{m}.csv")
        rp = os.path.join(root, f"ranked_{m}{a.ranked_suffix}.csv")
        if not (os.path.exists(ep) and os.path.exists(rp)):
            lines.append(f"--- {m}: missing inputs, skipped ---\n")
            continue

        edges = pd.read_csv(ep)
        nodes = pd.read_csv(os.path.join(root, f"subgraph_nodes_{m}.csv"))
        ids = nodes.root_id.to_numpy()
        idx = pd.Series(np.arange(len(ids)), index=ids)
        n = len(ids)
        src_i = edges.source.map(idx).to_numpy()
        dst_i = edges.target.map(idx).to_numpy()
        w = 1.0 / edges.syn_count.to_numpy(dtype=float)

        pool = idx[source_ids(nodes, m)].to_numpy()
        tgt = idx[nodes.loc[nodes.super_class.isin(DESCENDING), "root_id"]].to_numpy()
        if len(pool) == 0 or len(tgt) == 0:
            lines.append(f"--- {m}: no sources/targets, skipped ---\n")
            continue
        srcs = np.sort(rng.choice(pool, min(a.sources, len(pool)), replace=False))

        ranked = pd.read_csv(rp)
        ranked = ranked[ranked.root_id.isin(idx.index)].reset_index(drop=True)
        bands = {
            "top50": ranked.head(50).root_id.to_numpy(),
            "rank1000_2000": ranked.iloc[1000:2000].root_id.to_numpy(),
            "random_any": ranked.root_id.to_numpy(),
        }

        base = solve(src_i, dst_i, w, n, srcs, tgt)
        n_pairs = int(np.isfinite(base).sum())
        print(f"\n=== {m}: {n} nodes, {len(srcs)}x{len(tgt)} pairs "
              f"({n_pairs} connected)", flush=True)

        for band, bpool in bands.items():
            if len(bpool) == 0:
                continue
            pick = rng.choice(bpool, min(a.n, len(bpool)), replace=False)
            for r in pick:
                k = int(idx[r])
                ks, kt = srcs != k, tgt != k
                pct, cut = damage(base, solve(src_i, dst_i, w, n, srcs, tgt, {k}), ks, kt)
                rows.append(dict(root=os.path.basename(root) or "fafb", modality=m,
                                 band=band, root_id=r, detour_pct=pct, cut_pairs=cut))
            print(f"  {band} done", flush=True)

        df = pd.DataFrame([r for r in rows if r["modality"] == m])
        lines.append(f"--- {m} ---   {len(srcs)} sources x {len(tgt)} targets, "
                     f"{n_pairs} connected pairs")
        for band in bands:
            b = df[df.band == band]
            if not len(b):
                continue
            lines.append(f"  {band:<15} detour {b.detour_pct.mean():7.3f}% "
                         f"(max {b.detour_pct.max():7.3f}%)   "
                         f"neurons cutting >=1 pair: {int((b.cut_pairs > 0).sum())}/{len(b)}"
                         f"   max cut {int(b.cut_pairs.max())}")
        lines.append("")

    if rows:
        pd.DataFrame(rows).to_csv(os.path.join(root, "robustness.csv"), index=False)
    txt = "\n".join(lines) + "\n"
    with open(os.path.join(root, "robustness.txt"), "w") as f:
        f.write(txt)
    print("\n" + txt)


if __name__ == "__main__":
    main()
