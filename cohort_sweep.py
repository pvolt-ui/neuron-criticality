#!/usr/bin/env python
"""
cohort_sweep.py -- does criticality scale with cohort size, and is a cell type
more than the sum of its neurons?

celltype_ablation.py found one striking case: lLN2T_c's four copies do 11x the
damage of its best single copy. But almost every other validated type is a
bilateral pair (k=2), so "cell type" and "both copies" were the same experiment
and the size effect could not be separated from the coherence effect. This script
sweeps cohort size properly.

THE TWO QUESTIONS, SEPARATED
  1. SIZE      how does damage grow with the number of neurons removed, for
               random sets? That is the baseline curve any cohort must beat.
  2. COHERENCE at the same size AND the same betweenness rank band, does a real
               cell type do more damage than an arbitrary set of neurons?

  Matching on size alone is not enough: cell types drawn from the top of the
  ranking would beat random mid-ranked sets for trivial reasons. Every cell type
  here is compared against random sets matched on size AND drawn from the same
  rank band as that type's own members (rank-matched control), which isolates
  coherence.

SUPERADDITIVITY
  superadd = damage(whole cohort) / sum(damage(each member alone))
  > 1 means the cohort is more than the sum of its parts -- removing the copies
  together opens a hole that removing them one at a time never reveals, because
  each copy's traffic reroutes onto its siblings. This is the quantity the
  single-neuron deletion test structurally cannot see.

All damage is scored only over source->target pairs whose own endpoints survive
the deletion (see celltype_ablation.py).

Usage:  python3 cohort_sweep.py [--sources N] [--draws N] [--modality M]
Output: cohort_sweep.csv, cohort_sweep.txt
"""
import argparse
import os

import numpy as np
import pandas as pd

from celltype_ablation import damage, solve

ROOT = os.path.dirname(os.path.abspath(__file__))
META = os.path.join(ROOT, "data", "meta")
from pathways import MODALITIES, source_ids  # noqa: E402
DESCENDING = {"descending", "motor"}
SIZES = [1, 2, 4, 8, 16, 32]
N_SOURCES = 100
N_DRAWS = 10             # random sets per (size, band)
MAX_TYPES = 25           # cell types tested per modality, largest cohorts first
SEED = 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", type=int, default=N_SOURCES)
    ap.add_argument("--draws", type=int, default=N_DRAWS)
    ap.add_argument("--modality", default=None)
    a = ap.parse_args()

    rng = np.random.default_rng(SEED)
    types_tbl = pd.read_csv(os.path.join(META, "fafb_consolidated_cell_types.csv.gz"))[
        ["root_id", "primary_type"]]
    rows, lines = [], ["Cohort-size sweep -- size effect vs coherence effect", "=" * 70, ""]

    for m in ([a.modality] if a.modality else MODALITIES):
        edges = pd.read_csv(os.path.join(ROOT, f"subgraph_edges_{m}.csv"))
        nodes = pd.read_csv(os.path.join(ROOT, f"subgraph_nodes_{m}.csv"))
        ids = nodes.root_id.to_numpy()
        idx = pd.Series(np.arange(len(ids)), index=ids)
        n = len(ids)
        src_i = edges.source.map(idx).to_numpy()
        dst_i = edges.target.map(idx).to_numpy()
        w = 1.0 / edges.syn_count.to_numpy(dtype=float)

        pool = idx[source_ids(nodes, m)].to_numpy()
        tgt = idx[nodes.loc[nodes.super_class.isin(DESCENDING), "root_id"]].to_numpy()
        srcs = np.sort(rng.choice(pool, min(a.sources, len(pool)), replace=False))

        ranked = pd.read_csv(os.path.join(ROOT, f"ranked_{m}.csv"))
        ranked = ranked[ranked.root_id.isin(idx.index)].reset_index(drop=True)
        pos_of = {r: i for i, r in enumerate(ranked.root_id)}

        base = solve(src_i, dst_i, w, n, srcs, tgt)

        def hit(drop):
            d = set(int(x) for x in drop)
            ks = ~np.isin(srcs, list(d)) if d else None
            kt = ~np.isin(tgt, list(d)) if d else None
            return damage(base, solve(src_i, dst_i, w, n, srcs, tgt, d), ks, kt)

        print(f"\n=== {m}: {n} nodes, {len(srcs)} sources, {len(tgt)} targets", flush=True)

        # ---- 1. size curve: random sets from three rank bands ----------------
        bands = {"top200": ranked.head(200).root_id.to_numpy(),
                 "rank200_1000": ranked.iloc[200:1000].root_id.to_numpy(),
                 "rank1000_2000": ranked.iloc[1000:2000].root_id.to_numpy()}
        for band, bpool in bands.items():
            for k in SIZES:
                if k > len(bpool):
                    continue
                for _ in range(a.draws):
                    pick = idx[rng.choice(bpool, k, replace=False)].to_numpy()
                    pct, cut = hit(pick)
                    rows.append(dict(modality=m, kind="random", band=band, size=k,
                                     label=f"{band}", detour_pct=pct, cut_pairs=cut))
            print(f"  size curve {band} done", flush=True)

        # ---- 2. real cell types, rank-matched controls -----------------------
        tmap = types_tbl.set_index("root_id").primary_type
        node_type = pd.Series(ids, index=ids).map(tmap)
        counts = node_type.value_counts()
        # types with >=2 copies in the subgraph and at least one well-ranked member
        # rank types by their BEST member -- selecting by copy count instead would
        # fill the list with large, low-ranked types and drop the ones the study
        # actually makes claims about.
        best_pos = {t: min(pos_of.get(r, 10**9)
                           for r in node_type[node_type == t].index)
                    for t in counts[counts >= 2].index}
        cand = [t for t, p_ in sorted(best_pos.items(), key=lambda kv: kv[1])
                if p_ < 500][:MAX_TYPES]

        for t in cand:
            members = node_type[node_type == t].index.to_numpy()
            mi = idx[members].to_numpy()
            k = len(mi)
            pct, cut = hit(mi)
            singles = [hit([i])[0] for i in mi]
            ssum = float(np.nansum(singles))
            superadd = pct / ssum if ssum > 0 else np.nan

            # rank-matched control: same size, drawn from the same rank window
            positions = [pos_of.get(r, len(ranked) - 1) for r in members]
            lo, hi = max(0, min(positions) - 50), min(len(ranked), max(positions) + 50)
            window = ranked.iloc[lo:hi].root_id.to_numpy()
            ctl = []
            for _ in range(a.draws):
                if k > len(window):
                    break
                pick = idx[rng.choice(window, k, replace=False)].to_numpy()
                ctl.append(hit(pick)[0])
            ctl = np.array(ctl, dtype=float)
            # A rank-matched control band that does ~zero damage makes z explode
            # on any nonzero cohort effect. Flag those rather than quoting a huge
            # unstable z off a near-degenerate control distribution.
            csd = ctl.std(ddof=1) if len(ctl) > 1 else 0.0
            z = (pct - ctl.mean()) / csd if csd > 0 else np.nan
            degenerate = bool(csd > 0 and ctl.mean() < 0.01 * pct)

            rows.append(dict(modality=m, kind="celltype", band="rank_matched", size=k,
                             label=t, detour_pct=pct, cut_pairs=cut,
                             single_sum=ssum, best_single=float(np.nanmax(singles)),
                             superadd=superadd, z_vs_rankmatched=z,
                             ctl_mean=float(ctl.mean()) if len(ctl) else np.nan,
                             ctl_degenerate=degenerate,
                             median_rank=float(np.median(positions)) + 1))
            print(f"  {t:<12} k={k:<3} cohort {pct:7.3f}%  sum-of-singles {ssum:7.3f}%  "
                  f"superadd {superadd:5.2f}x  z {z:+.2f}"
                  f"{'  [near-zero control]' if degenerate else ''}", flush=True)

        df = pd.DataFrame([r for r in rows if r["modality"] == m])
        rnd = df[df.kind == "random"]
        ct = df[df.kind == "celltype"]

        lines.append(f"--- {m} ---")
        lines.append("  size curve (mean detour % of a random set of k neurons):")
        lines.append(f"    {'band':<15}" + "".join(f"{k:>9}" for k in SIZES))
        for band in bands:
            b = rnd[rnd.band == band]
            lines.append(f"    {band:<15}" + "".join(
                f"{b[b['size'] == k].detour_pct.mean():>9.3f}" if len(b[b['size'] == k])
                else f"{'-':>9}" for k in SIZES))
        if len(ct):
            sa = ct.superadd.dropna()
            lines.append("")
            lines.append(f"  cell types tested: {len(ct)}   "
                         f"superadditive (>1x): {int((sa > 1).sum())}/{len(sa)}   "
                         f"median {sa.median():.2f}x")
            solid = ct[(ct.z_vs_rankmatched > 2) & (~ct.ctl_degenerate)]
            lines.append(f"  beating rank-matched control at z>2: "
                         f"{int((ct.z_vs_rankmatched > 2).sum())}/{len(ct)}"
                         f"   (excluding near-zero-control cases: {len(solid)})")
            lines.append("")
            lines.append(f"  {'cell type':<13}{'k':>3}{'medrank':>8}{'cohort':>9}"
                         f"{'sum1by1':>9}{'superadd':>10}{'z':>8}  flag")
            for _, r in ct.sort_values("superadd", ascending=False).iterrows():
                lines.append(f"  {r.label:<13}{int(r['size']):>3}{r.median_rank:>8.0f}"
                             f"{r.detour_pct:>8.3f}%{r.single_sum:>8.3f}%"
                             f"{r.superadd:>9.2f}x{r.z_vs_rankmatched:>+8.2f}"
                             f"{'  near-zero ctl' if r.ctl_degenerate else ''}")
        lines.append("")

    res = pd.DataFrame(rows)
    res.to_csv(os.path.join(ROOT, "cohort_sweep.csv"), index=False)
    txt = "\n".join(lines) + "\n"
    with open(os.path.join(ROOT, "cohort_sweep.txt"), "w") as f:
        f.write(txt)
    print("\n" + txt)


if __name__ == "__main__":
    main()
