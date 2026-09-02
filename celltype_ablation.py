#!/usr/bin/env python
"""
celltype_ablation.py -- is the unit of criticality the neuron, or the cell type?

cross_modal_audit.py deleted one neuron at a time and found nothing indispensable:
zero sensory->descending pairs disconnected, at any rank. But fly neurons come in
bilateral pairs and cell-type cohorts, so that result may only show that the other
copy covers the loss. This script deletes an ENTIRE CELL TYPE -- every copy, both
hemispheres -- and re-solves.

THE CONTROL IS THE WHOLE EXPERIMENT
  Deleting 8 neurons will always damage a graph more than deleting 1, so raw
  cohort damage means nothing on its own. Every cell type is scored against
  SIZE-MATCHED random deletions drawn from the same subgraph:

    random_mid   k neurons drawn at random from betweenness ranks 1000-2000
                 -- what damage does removing k unremarkable neurons do?
    random_top   k neurons drawn at random from the top 200
                 -- controls for "well-ranked neurons are damaging" in general,
                 so a surviving effect is about cohort COHERENCE, not rank

  A cell type is interesting only if it beats BOTH, i.e. the copies of one type
  are collectively more load-bearing than k comparably-ranked neurons that do not
  form a type. That is the claim "the cell type is the functional unit".

MEASURES  (same solver as cross_modal_audit.py)
  cut_pairs    source->target pairs made unreachable -- the headline. Single-neuron
               deletion never cut a single pair in any pathway.
  detour_pct   mean % increase in weighted route length over surviving pairs

Usage:  python3 celltype_ablation.py [--sources N] [--controls N] [--modality M]
Output: celltype_ablation.csv, celltype_ablation.txt
"""
import argparse
import os

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

ROOT = os.path.dirname(os.path.abspath(__file__))
META = os.path.join(ROOT, "data", "meta")
from pathways import MODALITIES, source_ids  # noqa: E402
DESCENDING = {"descending", "motor"}
N_SOURCES = 100
N_CONTROLS = 12          # size-matched random draws per control band
SEED = 0


def solve(src_i, dst_i, w, n, sources, targets, drop=frozenset()):
    if drop:
        d = np.array(sorted(drop))
        keep = ~(np.isin(src_i, d) | np.isin(dst_i, d))
        s, t, ww = src_i[keep], dst_i[keep], w[keep]
    else:
        s, t, ww = src_i, dst_i, w
    m = coo_matrix((ww, (s, t)), shape=(n, n)).tocsr()
    return dijkstra(m, directed=True, indices=sources)[:, targets]


def damage(base, test, keep_src=None, keep_tgt=None):
    """Damage over pairs whose OWN endpoints survive the deletion.

    A deleted neuron that is itself a descending target trivially disconnects every
    pair routed to it -- that is bookkeeping, not a bottleneck. Several validated
    mechanosensory types ARE descending neurons, and random control draws hit
    targets by chance, so both sides must be scored on the same restricted pair
    set: sources and targets that were not themselves deleted.
    """
    b, t = base, test
    if keep_src is not None:
        b, t = b[keep_src], t[keep_src]
    if keep_tgt is not None:
        b, t = b[:, keep_tgt], t[:, keep_tgt]
    alive = np.isfinite(b)
    cut = int((alive & ~np.isfinite(t)).sum())
    both = alive & np.isfinite(t)
    if not both.any():
        return float("nan"), cut
    return 100.0 * (t[both] - b[both]).sum() / b[both].sum(), cut


def run(modality, n_sources, n_controls, rng):
    edges = pd.read_csv(os.path.join(ROOT, f"subgraph_edges_{modality}.csv"))
    nodes = pd.read_csv(os.path.join(ROOT, f"subgraph_nodes_{modality}.csv"))
    types = pd.read_csv(os.path.join(META, "fafb_consolidated_cell_types.csv.gz"))[
        ["root_id", "primary_type"]]

    ids = nodes.root_id.to_numpy()
    idx = pd.Series(np.arange(len(ids)), index=ids)
    n = len(ids)
    src_i = edges.source.map(idx).to_numpy()
    dst_i = edges.target.map(idx).to_numpy()
    w = 1.0 / edges.syn_count.to_numpy(dtype=float)

    pool = idx[source_ids(nodes, modality)].to_numpy()
    tgt = idx[nodes.loc[nodes.super_class.isin(DESCENDING), "root_id"]].to_numpy()
    srcs = np.sort(rng.choice(pool, min(n_sources, len(pool)), replace=False))

    ranked = pd.read_csv(os.path.join(ROOT, f"ranked_{modality}.csv"))
    rank_of = dict(zip(ranked.root_id, ranked["rank"]))
    nullb = pd.read_csv(os.path.join(ROOT, f"null_degree_{modality}.csv"))
    validated = nullb[(nullb.p_emp <= 0.05) & (nullb["rank"] <= 25)]

    # every copy of each validated cell type that lives in this subgraph
    tmap = types.set_index("root_id").primary_type
    node_type = pd.Series(ids, index=ids).map(tmap)
    cohorts = {}
    for t in validated.primary_type.dropna().unique():
        members = node_type[node_type == t].index.to_numpy()
        if len(members):
            cohorts[t] = idx[members].to_numpy()

    mid_pool = idx[[r for r in ranked.iloc[1000:2000].root_id if r in idx.index]].to_numpy()
    top_pool = idx[[r for r in ranked.head(200).root_id if r in idx.index]].to_numpy()

    print(f"\n=== {modality}: {n} nodes, {len(srcs)} sources, {len(tgt)} targets, "
          f"{len(cohorts)} validated cell types", flush=True)

    base = solve(src_i, dst_i, w, n, srcs, tgt)
    rows = []

    def hit(drop):
        """Damage of deleting `drop`, scored only on pairs with surviving endpoints."""
        d = set(int(x) for x in drop)
        ks = ~np.isin(srcs, list(d)) if d else None
        kt = ~np.isin(tgt, list(d)) if d else None
        return damage(base, solve(src_i, dst_i, w, n, srcs, tgt, d), ks, kt)

    # size-matched controls, computed once per distinct cohort size
    ctl_cache = {}
    for k in sorted({len(v) for v in cohorts.values()}):
        for band, bpool in [("random_mid", mid_pool), ("random_top", top_pool)]:
            vals = []
            for _ in range(n_controls):
                pick = rng.choice(bpool, min(k, len(bpool)), replace=False)
                pct, cut = hit(pick)
                vals.append((pct, cut))
                rows.append(dict(modality=modality, label=f"{band}(k={k})", group=band,
                                 size=k, detour_pct=pct, cut_pairs=cut))
            ctl_cache[(k, band)] = np.array(vals)
        print(f"  controls k={k} done", flush=True)

    for t, members in sorted(cohorts.items(), key=lambda kv: -len(kv[1])):
        k = len(members)
        pct, cut = hit(members)
        # single best copy of the same type, for the neuron-vs-type contrast
        best = min(members, key=lambda i: rank_of.get(ids[i], 10 ** 9))
        spct, scut = hit([best])
        z = {}
        for band in ("random_mid", "random_top"):
            c = ctl_cache[(k, band)][:, 0]
            z[band] = (pct - c.mean()) / c.std(ddof=1) if c.std(ddof=1) > 0 else np.nan
        rows.append(dict(modality=modality, label=t, group="celltype", size=k,
                         detour_pct=pct, cut_pairs=cut,
                         single_detour_pct=spct, single_cut_pairs=scut,
                         z_vs_mid=z["random_mid"], z_vs_top=z["random_top"]))
        print(f"  {t:<12} k={k:<3} detour {pct:7.3f}%  cut {cut:<5} "
              f"(single copy: {spct:6.3f}%, cut {scut})  "
              f"z_top {z['random_top']:+.2f}", flush=True)

    return pd.DataFrame(rows), base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", type=int, default=N_SOURCES)
    ap.add_argument("--controls", type=int, default=N_CONTROLS)
    ap.add_argument("--modality", default=None)
    a = ap.parse_args()

    rng = np.random.default_rng(SEED)
    out, lines = [], ["Cell-type ablation -- is the unit of criticality the neuron or the type?",
                      "=" * 74, ""]
    for m in ([a.modality] if a.modality else MODALITIES):
        df, _ = run(m, a.sources, a.controls, rng)
        out.append(df)
        ct = df[df.group == "celltype"]
        lines.append(f"--- {m} ---")
        for band in ("random_mid", "random_top"):
            c = df[df.group == band]
            lines.append(f"  {band:<11} detour {c.detour_pct.mean():6.3f}% "
                         f"cut {c.cut_pairs.mean():6.1f} (size-matched draws)")
        lines.append(f"  cell types that cut >=1 pair: "
                     f"{int((ct.cut_pairs > 0).sum())}/{len(ct)}   "
                     f"single-copy deletions that cut >=1: "
                     f"{int((ct.single_cut_pairs > 0).sum())}/{len(ct)}")
        lines.append("")
        lines.append(f"  {'cell type':<13}{'n':>3}{'detour':>9}{'cut':>7}"
                     f"{'1-copy':>9}{'1-cut':>7}{'z vs top':>10}")
        for _, r in ct.sort_values("detour_pct", ascending=False).iterrows():
            lines.append(f"  {r.label:<13}{int(r['size']):>3}{r.detour_pct:>8.3f}%"
                         f"{int(r.cut_pairs):>7}{r.single_detour_pct:>8.3f}%"
                         f"{int(r.single_cut_pairs):>7}{r.z_vs_top:>+10.2f}")
        lines.append("")

    res = pd.concat(out, ignore_index=True)
    res.to_csv(os.path.join(ROOT, "celltype_ablation.csv"), index=False)
    txt = "\n".join(lines) + "\n"
    with open(os.path.join(ROOT, "celltype_ablation.txt"), "w") as f:
        f.write(txt)
    print("\n" + txt)


if __name__ == "__main__":
    main()
