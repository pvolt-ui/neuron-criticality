#!/usr/bin/env python
"""
neuropil.py -- assign each neuron a dominant neuropil from its synapses.

FAFB's per-neuron metadata tables carry no neuropil column, which is why the
project previously characterized bottlenecks by cell type / neurotransmitter /
sub-class only. The neuropil *is* available, just per-connection rather than
per-neuron: Codex's connections export gives a neuropil and a synapse count for
every (pre, post, neuropil) row.

So we define a neuron's neuropil as where its synapses actually are: sum
syn_count per (neuron, neuropil) over both roles the neuron plays (as the
presynaptic partner and as the postsynaptic partner), then take the argmax.

`neuropil_frac` reports what share of the neuron's synapses fall in that top
neuropil -- treat a neuron with a low frac as genuinely distributed across
neuropils rather than as belonging to the winner.

Output (cached):
  neuron_neuropil.csv   root_id, neuropil, neuropil_frac, total_syn
"""
import os

import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
CONNECTIONS = os.path.join(ROOT, "data", "meta", "fafb_connections.csv.gz")
CACHE = os.path.join(ROOT, "neuron_neuropil.csv")


def build(force=False):
    """Return root_id -> dominant neuropil, building and caching if needed."""
    if os.path.exists(CACHE) and not force:
        return pd.read_csv(CACHE)

    print("  building neuron -> neuropil map from connections...")
    conn = pd.read_csv(
        CONNECTIONS, usecols=["pre_root_id", "post_root_id", "neuropil", "syn_count"]
    )

    # A synapse in neuropil N counts toward both partners' presence in N.
    pre = conn[["pre_root_id", "neuropil", "syn_count"]].rename(
        columns={"pre_root_id": "root_id"}
    )
    post = conn[["post_root_id", "neuropil", "syn_count"]].rename(
        columns={"post_root_id": "root_id"}
    )
    both = pd.concat([pre, post], ignore_index=True)

    per_np = both.groupby(["root_id", "neuropil"], as_index=False, sort=False)["syn_count"].sum()
    total = per_np.groupby("root_id", as_index=False, sort=False)["syn_count"].sum()
    total = total.rename(columns={"syn_count": "total_syn"})

    # argmax neuropil per neuron
    per_np = per_np.sort_values("syn_count", ascending=False)
    top = per_np.drop_duplicates("root_id", keep="first")

    out = top.merge(total, on="root_id", how="left")
    out["neuropil_frac"] = out["syn_count"] / out["total_syn"]
    out = out[["root_id", "neuropil", "neuropil_frac", "total_syn"]]

    out.to_csv(CACHE, index=False)
    print(f"  cached {len(out)} neurons -> {CACHE}")
    return out


if __name__ == "__main__":
    df = build(force=True)
    print(f"\n{len(df)} neurons assigned a dominant neuropil")
    print(f"median dominance fraction: {df.neuropil_frac.median():.2f}")
    print("\nmost common dominant neuropils:")
    print(df["neuropil"].value_counts().head(15).to_string())
