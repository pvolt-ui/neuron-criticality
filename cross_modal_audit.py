#!/usr/bin/env python
"""
cross_modal_audit.py -- are the five cross-modal bottlenecks genuine convergence
points, or artifacts of the 2-hop cutoff?

Betweenness says a neuron carries many shortest sensory->descending paths. It does
NOT say the pathway would suffer without it: if a parallel route of near-equal
weight exists, the neuron is on the shortest path but not indispensable. This
script runs the test betweenness cannot -- delete the neuron and re-solve.

TEST (per modality, per neuron)
  Weighted distance = 1/syn_count, so "short" = strongly connected. For a sample
  of sensory sources, solve all-pairs shortest distance to every descending
  target, with and without the neuron. Two damages are recorded:
    detour_pct    mean % increase in source->target distance over pairs that
                  stay connected -- how much longer the strong route gets
    cut_pairs     source->target pairs that become unreachable entirely

CONTROLS  (a raw delta is meaningless without them)
  top50    other top-50 betweenness neurons of the same modality. The question
           "is this cross-modal neuron special" only matters relative to the
           ordinary bottleneck it is being ranked alongside.
  mid      neurons ranked 1000-2000, i.e. unremarkable members of the same graph.
  A candidate is interesting only if its damage exceeds the top50 control
  distribution, reported as a z-score against it.

CUTOFF ARTIFACT CHECK
  hop distance from the nearest sensory source and to the nearest descending
  target, unweighted. A neuron sitting at exactly the 2-hop boundary on the side
  that the subgraph construction truncated is a cutoff-sensitivity risk, and is
  flagged; one sitting strictly inside the pathway is not.

Output: cross_modal_audit.csv, cross_modal_audit.txt
"""
import os

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

ROOT = os.path.dirname(os.path.abspath(__file__))
from pathways import MODALITIES, source_ids  # noqa: E402
DESCENDING = {"descending", "motor"}
N_SOURCES = 100          # sampled sensory sources per modality
N_CONTROL = 12           # control neurons drawn per control band
SEED = 0


def load(modality):
    edges = pd.read_csv(os.path.join(ROOT, f"subgraph_edges_{modality}.csv"))
    nodes = pd.read_csv(os.path.join(ROOT, f"subgraph_nodes_{modality}.csv"))
    ids = nodes.root_id.to_numpy()
    idx = pd.Series(np.arange(len(ids)), index=ids)
    return edges, nodes, ids, idx


def solve(src_i, dst_i, w, n, sources, targets, drop=None):
    """Mean weighted source->target distance matrix, optionally deleting a node."""
    if drop is None:
        s, d, ww = src_i, dst_i, w
    else:
        keep = (src_i != drop) & (dst_i != drop)
        s, d, ww = src_i[keep], dst_i[keep], w[keep]
    m = coo_matrix((ww, (s, d)), shape=(n, n)).tocsr()
    return dijkstra(m, directed=True, indices=sources)[:, targets]


def damage(base, test, keep_src=None, keep_tgt=None):
    """detour % on surviving pairs, and count of pairs cut outright.

    Scored only over pairs whose OWN endpoints survive: deleting a neuron that is
    itself a sensory source or a descending target trivially kills every pair it
    is an endpoint of, which is bookkeeping rather than bottleneck behaviour.
    Candidates are all interneurons, but control draws hit endpoints by chance, so
    both sides must be scored on the same restricted pair set.
    """
    if keep_src is not None:
        base, test = base[keep_src], test[keep_src]
    if keep_tgt is not None:
        base, test = base[:, keep_tgt], test[:, keep_tgt]
    alive = np.isfinite(base)
    cut = int((alive & ~np.isfinite(test)).sum())
    both = alive & np.isfinite(test)
    if not both.any():
        return float("nan"), cut, int(alive.sum())
    pct = 100.0 * (test[both] - base[both]).sum() / base[both].sum()
    return pct, cut, int(alive.sum())


def hops(src_i, dst_i, n, sources, targets):
    """Unweighted hop distance from nearest source, and to nearest target."""
    ones = np.ones(len(src_i))
    fwd = coo_matrix((ones, (src_i, dst_i)), shape=(n, n)).tocsr()
    rev = coo_matrix((ones, (dst_i, src_i)), shape=(n, n)).tocsr()
    from_src = dijkstra(fwd, directed=True, indices=sources, unweighted=True).min(axis=0)
    to_tgt = dijkstra(rev, directed=True, indices=targets, unweighted=True).min(axis=0)
    return from_src, to_tgt


def main():
    import argparse, sys
    _ap = argparse.ArgumentParser(); _ap.add_argument('--modality', nargs='*', default=None)
    _a, _ = _ap.parse_known_args()
    mods = _a.modality or MODALITIES
    rng = np.random.default_rng(SEED)
    shared = pd.read_csv(os.path.join(ROOT, "cross_modal_bottlenecks.csv"))
    rows, lines = [], ["Cross-modal bottleneck audit -- node-deletion test", "=" * 68, ""]

    for m in mods:
        edges, nodes, ids, idx = load(m)
        n = len(ids)
        src_i = edges.source.map(idx).to_numpy()
        dst_i = edges.target.map(idx).to_numpy()
        w = 1.0 / edges.syn_count.to_numpy(dtype=float)

        sensory = source_ids(nodes, m)
        targets_id = nodes.loc[nodes.super_class.isin(DESCENDING), "root_id"]
        tgt = idx[targets_id].to_numpy()
        pool = idx[sensory].to_numpy()
        srcs = np.sort(rng.choice(pool, min(N_SOURCES, len(pool)), replace=False))

        ranked = pd.read_csv(os.path.join(ROOT, f"ranked_{m}.csv"))
        top50 = ranked.head(50).root_id.tolist()
        mid = ranked.iloc[1000:2000].root_id.tolist()

        cands = [r for r in shared.root_id if r in idx.index and r in set(top50)]
        ctl_top = list(rng.choice([r for r in top50 if r not in cands], N_CONTROL, replace=False))
        ctl_mid = list(rng.choice(mid, N_CONTROL, replace=False))

        print(f"\n=== {m}: {n} nodes, {len(srcs)} sources, {len(tgt)} targets, "
              f"{len(cands)} candidates", flush=True)

        from_src, to_tgt = hops(src_i, dst_i, n, srcs, tgt)
        base = solve(src_i, dst_i, w, n, srcs, tgt)

        res = {}
        for group, members in [("candidate", cands), ("top50", ctl_top), ("mid", ctl_mid)]:
            for r in members:
                k = int(idx[r])
                ks = srcs != k
                kt = tgt != k
                pct, cut, alive = damage(
                    base, solve(src_i, dst_i, w, n, srcs, tgt, drop=k), ks, kt)
                res[r] = dict(modality=m, root_id=r, group=group,
                              rank=int(ranked.index[ranked.root_id == r][0]) + 1,
                              detour_pct=pct, cut_pairs=cut, live_pairs=alive,
                              hops_from_sensory=float(from_src[k]),
                              hops_to_descending=float(to_tgt[k]))
                print(f"  {group:9s} {r}  detour {pct:6.3f}%  cut {cut}", flush=True)

        df = pd.DataFrame(res.values())
        ref = df[df.group == "top50"].detour_pct
        mu, sd = ref.mean(), ref.std(ddof=1)
        df["z_vs_top50"] = (df.detour_pct - mu) / sd if sd > 0 else np.nan
        rows.append(df)

        lines.append(f"--- {m} ---")
        lines.append(f"  {len(srcs)} sampled sources x {len(tgt)} descending targets"
                     f"   ({int(np.isfinite(base).sum())} connected pairs)")
        lines.append(f"  top-50 control detour: {mu:.3f}% +/- {sd:.3f}"
                     f"   (max {ref.max():.3f}%)")
        mref = df[df.group == "mid"].detour_pct
        lines.append(f"  rank-1000+ control:    {mref.mean():.3f}% +/- {mref.std(ddof=1):.3f}")
        lines.append("")
        for _, r in df[df.group == "candidate"].iterrows():
            ct = shared.loc[shared.root_id == r.root_id].iloc[0]
            flag = ""
            if r.hops_from_sensory >= 2 and r.hops_to_descending >= 2:
                flag = "   [both sides at cutoff -- artifact risk]"
            lines.append(f"  {int(r.root_id)}  {ct.primary_type:<9s} {ct.neuropil:<7s} "
                         f"rank {int(r['rank']):>3d}  detour {r.detour_pct:6.3f}%  "
                         f"z={r.z_vs_top50:+5.2f}  cut {int(r.cut_pairs)}  "
                         f"hops {int(r.hops_from_sensory)}->{int(r.hops_to_descending)}{flag}")
        lines.append("")

    out = pd.concat(rows, ignore_index=True)
    out.to_csv(os.path.join(ROOT, "cross_modal_audit.csv"), index=False)
    with open(os.path.join(ROOT, "cross_modal_audit.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
