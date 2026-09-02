#!/usr/bin/env python
"""
cross_modal_overlap.py -- Phase D: find neurons that are top-50 betweenness
bottlenecks in 2 or all 3 sensory modalities, and characterize them. This is
the payoff cross-modal result of Project 7.

Input:
  characterized_<modality>.csv   from characterize.py (top-50 per modality,
                                  already joined to cell type / NT / sub_class)

Output:
  cross_modal_bottlenecks.csv    one row per neuron in 2+ top-50 lists
  cross_modal_summary.txt        set-overlap counts + a short characterization
"""
import os
from collections import defaultdict

import pandas as pd

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
from pathways import MODALITIES, source_ids  # noqa: E402


def main():
    per_modality = {}
    for modality in MODALITIES:
        df = pd.read_csv(os.path.join(OUT_DIR, f"characterized_{modality}.csv"))
        per_modality[modality] = df.set_index("root_id")

    root_to_modalities = defaultdict(list)
    for modality, df in per_modality.items():
        for root_id in df.index:
            root_to_modalities[root_id].append(modality)

    shared = {rid: mods for rid, mods in root_to_modalities.items() if len(mods) >= 2}
    print(f"Neurons in 2+ modalities' top-50: {len(shared)}")
    print(f"Neurons in all modalities' top-50: {sum(1 for m in shared.values() if len(m) == 3)}")

    rows = []
    for root_id, mods in shared.items():
        first = per_modality[mods[0]].loc[root_id]
        row = {
            "root_id": root_id,
            "modalities": "+".join(sorted(mods)),
            "n_modalities": len(mods),
            "primary_type": first["primary_type"],
            "neuropil": first["neuropil"],
            "nt_type": first["nt_type"],
            "sub_class": first["sub_class"],
            "nerve": first["nerve"],
        }
        for modality in MODALITIES:
            row[f"betweenness_{modality}"] = (
                per_modality[modality].loc[root_id, "betweenness"] if modality in mods else None
            )
        rows.append(row)

    overlap_df = pd.DataFrame(rows).sort_values("n_modalities", ascending=False)
    out_csv = os.path.join(OUT_DIR, "cross_modal_bottlenecks.csv")
    overlap_df.to_csv(out_csv, index=False)
    print(f"saved {out_csv}")

    lines = []
    lines.append("Cross-modal bottleneck overlap (top-50 betweenness per modality)")
    lines.append("=" * 65)
    for modality in MODALITIES:
        lines.append(f"{modality}: 50 candidates")
    lines.append("")
    lines.append(f"In 2+ modalities: {len(shared)}")
    lines.append(f"In all modalities: {sum(1 for m in shared.values() if len(m) == 3)}")
    lines.append("")
    if len(overlap_df):
        lines.append("Cell types among shared bottlenecks:")
        lines.append(overlap_df["primary_type"].value_counts().to_string())
        lines.append("")
        lines.append("Neuropils among shared bottlenecks:")
        lines.append(overlap_df["neuropil"].value_counts().to_string())
        lines.append("")
        lines.append("Neurotransmitters among shared bottlenecks:")
        lines.append(overlap_df["nt_type"].value_counts().to_string())
    else:
        lines.append("No neurons appear as a top-50 bottleneck in more than one modality "
                      "at this 2-hop / synapse-weighted / top-50 scope.")

    summary = "\n".join(lines)
    print("\n" + summary)
    out_txt = os.path.join(OUT_DIR, "cross_modal_summary.txt")
    with open(out_txt, "w") as f:
        f.write(summary + "\n")
    print(f"\nsaved {out_txt}")


if __name__ == "__main__":
    main()
