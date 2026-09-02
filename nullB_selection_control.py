#!/usr/bin/env python
"""
nullB_selection_control.py -- how many of Null B's "survivors" are a
selection artifact?

THE PROBLEM
  null_degree_preserving.py picks the top-50 neurons by REAL betweenness and
  then asks, for each, whether its real value exceeds its own degree-preserving
  null distribution. But the top-50 were selected for having extreme realised
  values. Even in a graph with no positional structure at all -- a pure
  configuration-model draw -- the 50 nodes that happen to land highest will sit
  above their own per-node null means, simply because they were chosen as the
  maximum (winner's curse / regression to the mean). So "37/50 survive" has an
  unknown false-positive floor.

THE CONTROL
  Run the whole Null B procedure on a graph that is KNOWN to have no positional
  structure: take one degree-preserving shuffle of the real subgraph, treat it
  as if it were the real data (compute betweenness, take ITS top-50), and test
  those 50 against `trials` further shuffles of the same graph. Everything is
  identical to the real analysis except that, by construction, every "survivor"
  is a false positive. The survival count that comes out is the selection-bias
  floor against which the real count must be read.

  Repeated for `reps` independent pseudo-real graphs so the floor has an error
  bar. Same sampled sources, same swap factor, same BH-FDR on p_z as Null B.

READ
  real survivors (from null_degree_<m>.csv)  vs  control survivors (mean ± sd).
  If the real count sits well above the control band, the Null B result stands
  net of selection. The z-score distribution of control survivors also tells you
  how large a z the selection effect alone can manufacture.

Usage:  python3 nullB_selection_control.py [--modality M ...] [--trials 50] [--reps 3] [--sources 100]
Output: nullB_selection_control_<m>.csv, nullB_selection_control.txt (appended)
"""
import argparse
import os
import time

import numpy as np
import pandas as pd

from null_degree_preserving import (betweenness, double_edge_swap, benjamini_hochberg,
                                    DESCENDING, TOP_N)
from pathways import MODALITIES, source_ids
from scipy.stats import norm

ROOT = os.path.dirname(os.path.abspath(__file__))


def survivors(real, null):
    mu, sd = null.mean(axis=0), null.std(axis=0, ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        z = np.where(sd > 0, (real - mu) / sd, np.inf)
    p_emp = ((null >= real).sum(axis=0) + 1) / (null.shape[0] + 1)
    q_z = benjamini_hochberg(norm.sf(z))
    q_emp = benjamini_hochberg(p_emp)
    return z, q_z, q_emp


def run(modality, trials, reps, n_sources, seed=1000):
    rng = np.random.default_rng(seed)
    edges = pd.read_csv(os.path.join(ROOT, f"subgraph_edges_{modality}.csv"))
    nodes_df = pd.read_csv(os.path.join(ROOT, f"subgraph_nodes_{modality}.csv"))
    nodes = nodes_df.root_id.tolist()
    src, dst = edges.source.to_numpy(), edges.target.to_numpy()
    w = edges.syn_count.to_numpy(dtype=float)
    pool = source_ids(nodes_df, modality).to_numpy()
    targets = nodes_df.loc[nodes_df.super_class.isin(DESCENDING), "root_id"].tolist()
    # same seed-0 source sample as null_degree_preserving.py
    sources = sorted(np.random.default_rng(0).choice(pool, min(n_sources, len(pool)),
                                                    replace=False).tolist())
    print(f"[{modality}] {len(nodes)} nodes, {len(src)} edges, {len(sources)} sources, "
          f"{len(targets)} targets; {reps} pseudo-real graphs x {trials} trials", flush=True)

    rows = []
    for rep in range(reps):
        t0 = time.time()
        # pseudo-real graph: one shuffle, treated as data
        ps, pd_ = double_edge_swap(src, dst, rng)
        bt = betweenness(ps, pd_, w, nodes, sources, targets)
        ranked = sorted(bt.items(), key=lambda kv: -kv[1])
        top = [r for r, _ in ranked[:TOP_N]]
        real_v = np.array([bt[r] for r in top])
        null = np.zeros((trials, TOP_N))
        for t in range(trials):
            s2, d2 = double_edge_swap(ps, pd_, rng)
            b2 = betweenness(s2, d2, w, nodes, sources, targets)
            null[t] = [b2.get(r, 0.0) for r in top]
        z, q_z, q_emp = survivors(real_v, null)
        n_qz = int((q_z <= 0.05).sum()); n_qz25 = int((q_z[:25] <= 0.05).sum())
        n_qe = int((q_emp <= 0.05).sum())
        fz = z[np.isfinite(z)]
        rows.append(dict(modality=modality, rep=rep, trials=trials,
                         surv_qz_top50=n_qz, surv_qz_top25=n_qz25, surv_qemp_top50=n_qe,
                         median_z=float(np.median(fz)), max_z=float(fz.max()),
                         seconds=time.time() - t0))
        print(f"  rep {rep}: survivors q_z<=.05  top50 {n_qz}/50  top25 {n_qz25}/25   "
              f"median z {np.median(fz):.2f}  max z {fz.max():.1f}   ({time.time()-t0:.0f}s)",
              flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(ROOT, f"nullB_selection_control_{modality}.csv"), index=False)

    # compare to the real Null B result
    rp = os.path.join(ROOT, f"null_degree_{modality}.csv")
    real_line = "(null_degree_<m>.csv not found)"
    if os.path.exists(rp):
        r = pd.read_csv(rp)
        real_line = (f"REAL     survivors q_z<=.05: top50 {int((r.q_z<=.05).sum())}/50  "
                     f"top25 {int((r.q_z.head(25)<=.05).sum())}/25   "
                     f"median z {np.median(r.z[np.isfinite(r.z)]):.2f}  "
                     f"max z {r.z[np.isfinite(r.z)].max():.1f}")
    ctl = (f"CONTROL  survivors q_z<=.05: top50 {out.surv_qz_top50.mean():.1f} ± "
           f"{out.surv_qz_top50.std(ddof=0):.1f}  top25 {out.surv_qz_top25.mean():.1f} ± "
           f"{out.surv_qz_top25.std(ddof=0):.1f}   median z {out.median_z.mean():.2f}  "
           f"max z {out.max_z.mean():.1f}   ({reps} pseudo-real graphs, {trials} trials each)")
    txt = f"\n=== {modality} ===\n{real_line}\n{ctl}\n"
    print(txt, flush=True)
    with open(os.path.join(ROOT, "nullB_selection_control.txt"), "a") as fh:
        fh.write(txt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modality", nargs="*", default=None)
    ap.add_argument("--trials", type=int, default=50)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--sources", type=int, default=100)
    a = ap.parse_args()
    for m in (a.modality or MODALITIES):
        run(m, a.trials, a.reps, a.sources)


if __name__ == "__main__":
    main()
