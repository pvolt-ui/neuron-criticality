#!/usr/bin/env python
"""
groundtruth_register.py -- freeze the cell-type list for the literature screen
BEFORE any searching happens.

Why pre-register: the earlier targeted check searched the types where evidence was
likely to exist and found agreement. That is a biased sample -- searching where you
expect hits inflates the apparent hit rate. This writes the full list first, so the
screen has to report the nulls and the uncharacterized too.

TWO ARMS
  validated   cell types of the validated top-25 (rank <= 25 and Null B FDR
              q_z <= 0.05), pooled over the three pathways
  control     cell types drawn from betweenness ranks 1000-2000 of the same
              pathways, matched in count. Without this arm "40% of validated
              types are characterized" is uninterpretable: the fly literature is
              biased toward large, named, accessible cells, and those are exactly
              the ones a centrality metric also favours. The control measures that
              background rate.

NAMED VS PLACEHOLDER
  Codex types like CB0109 / CB3916 are placeholder identifiers for cells with no
  published name. They are recorded as `placeholder` and count as uncharacterized
  by construction -- a handful are spot-checked in the screen to justify that.
  Only `named` types are individually searched.

Output: groundtruth_register.csv  (the frozen list; do not regenerate after searching)
"""
import os
import re

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
META = os.path.join(ROOT, "data", "meta")
from pathways import MODALITIES, source_ids  # noqa: E402
PLACEHOLDER = re.compile(r"^(CB|SLP|SMP|LHPV|LHAV|PS|PVLP|AVLP|IB|ATL|VES|CRE|LAL|WED|SAD)\d+[a-z]?$")
SEED = 0


def main():
    rng = np.random.default_rng(SEED)
    types = pd.read_csv(os.path.join(META, "fafb_consolidated_cell_types.csv.gz"))[
        ["root_id", "primary_type"]].set_index("root_id").primary_type

    rows = []
    for m in MODALITIES:
        nb = pd.read_csv(os.path.join(ROOT, f"null_degree_{m}.csv"))
        val = nb[(nb.q_z <= 0.05) & (nb["rank"] <= 25)]
        for t in sorted(set(val.primary_type.dropna().astype(str)) - {""}):
            rows.append(dict(arm="validated", modality=m, primary_type=t))

        ranked = pd.read_csv(os.path.join(ROOT, f"ranked_{m}.csv"))
        mid = ranked.iloc[1000:2000].root_id.map(types).dropna().astype(str)
        mid = sorted(set(mid) - {""})
        n = len(set(val.primary_type.dropna().astype(str)) - {""})
        pick = rng.choice(mid, min(n, len(mid)), replace=False) if mid else []
        for t in sorted(pick):
            rows.append(dict(arm="control", modality=m, primary_type=t))

    df = pd.DataFrame(rows).drop_duplicates(subset=["arm", "primary_type"])
    df["kind"] = np.where(df.primary_type.str.match(PLACEHOLDER), "placeholder", "named")
    # columns the screen fills in; frozen empty here
    for c in ["characterized", "evidence", "verdict", "source"]:
        df[c] = ""
    df = df.sort_values(["arm", "modality", "primary_type"], ignore_index=True)
    df.to_csv(os.path.join(ROOT, "groundtruth_register.csv"), index=False)

    print(df.groupby(["arm", "kind"]).size().to_string())
    print(f"\ntotal {len(df)} types; named to search: "
          f"{int((df.kind == 'named').sum())}")
    for arm in ["validated", "control"]:
        named = df[(df.arm == arm) & (df.kind == "named")].primary_type.tolist()
        print(f"\n{arm} named ({len(named)}): {', '.join(named)}")


if __name__ == "__main__":
    main()
