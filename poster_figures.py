#!/usr/bin/env python
"""
poster_figures.py -- the figure set for the end-of-August poster.

The old figures (figure_top_celltypes_*.png, figure_top_neuropils_*.png) charted
the raw top-50 betweenness lists. Those lists are superseded: Null B shows roughly
a third of ranks 26-50 are degree artifacts, and one named headline neuron
(lLN2F_b) fails the null outright. Everything here is built from the VALIDATED set
-- top-50 neurons that beat the degree-preserving null at p <= 0.05 -- and the
narrative figures are the ones the poster now actually argues:

  fig1_null_validation.png    the top-ranked neurons beat their own degree
  fig2_metric_disagreement.png  which "importance" metric you pick decides the answer
  fig3_deletion_damage.png    structured, but redundant -- nothing is indispensable
  fig4_validated_<modality>.png   what the surviving bottlenecks are (cell type + neuropil)

Palette: categorical slots 1-3 (blue/orange/aqua) assigned to modalities in fixed
order and never cycled; status good/critical for pass/fail. Validated with the
dataviz palette validator (all checks pass; aqua sits below 3:1 on the light
surface, so every bar carries a direct value label -- the relief rule).
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
from pathways import MODALITIES, source_ids  # noqa: E402

# categorical slots 1-3, fixed order, one per modality -- colour follows the
# entity, never its rank
COLOR = {"olfactory": "#2a78d6", "mechanosensory": "#eb6834", "visual": "#1baf7a"}
GOOD, CRITICAL = "#0ca30c", "#d03b3b"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e2e1dd"
SURFACE = "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "text.color": INK,
    "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False,
    "grid.color": GRID, "grid.linewidth": 1.0, "grid.linestyle": "-",
    "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold",
})


def save(fig, name):
    p = os.path.join(ROOT, name)
    fig.savefig(p, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {name}")


def validated(modality):
    """Top-50 neurons annotated with their Null B verdict."""
    return pd.read_csv(os.path.join(ROOT, f"null_degree_{modality}.csv"))


# ---------------------------------------------------------------- figure 1
def fig_null_validation():
    """Rank vs z against the degree-preserving null, small multiples by pathway.

    Log y because z spans 0.1 to 140. Pass/fail is status colour AND marker shape
    AND a labelled threshold line -- never colour alone.
    """
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), sharey=True)
    handles = None
    for ax, m in zip(axes, MODALITIES):
        d = validated(m)
        z = d.z.replace([np.inf, -np.inf], np.nan).clip(lower=0.05)
        ok = d.q_z <= 0.05
        h1 = ax.scatter(d["rank"][ok], z[ok], s=26, color=GOOD, zorder=3,
                        label="beats null (FDR q ≤ 0.05)")
        h2 = ax.scatter(d["rank"][~ok], z[~ok], s=34, facecolors="none",
                        edgecolors=CRITICAL, linewidths=1.6, marker="s", zorder=3,
                        label="fails null")
        handles = [h1, h2]
        ax.axvline(25.5, color=INK2, lw=1.0, ls=(0, (4, 3)), zorder=2)
        ax.set_yscale("log")
        ax.set_ylim(0.035, 3000)
        ax.set_title(f"{m}  —  {int(ok.sum())}/50 beat null", color=COLOR[m])
        ax.set_xlabel("betweenness rank")
        ax.grid(axis="y", zorder=0)
        ax.text(24.2, 1600, "top 25", fontsize=7.5, color=INK2, ha="right")
    axes[0].set_ylabel("z vs degree-preserving null")
    fig.legend(handles=handles, frameon=False, fontsize=8.5, ncols=2,
               loc="upper center", bbox_to_anchor=(0.5, 0.03))
    fig.suptitle("Top-ranked bottlenecks beat a null that preserves their exact degree",
                 fontsize=11, fontweight="bold", y=1.02)
    fig.text(0.5, -0.10, "Null-failing neurons with z ≤ 0 are drawn at the axis floor. "
             "Degree, out-synapse total and in/out-degree are held fixed by the null; "
             "only the identity of each neuron's partners is shuffled.",
             ha="center", fontsize=7.5, color=INK2)
    save(fig, "fig1_null_validation.png")


# ---------------------------------------------------------------- figure 2
def fig_metric_disagreement():
    """How much each metric's top-50 overlaps weighted betweenness's top-50.

    One axis, three series (pathways) in fixed categorical order, direct value
    labels on every bar, chance expectation drawn as a reference line.
    """
    metrics = ["bw_unweighted", "total_syn", "in_deg", "out_deg", "influence", "traversal"]
    nice = {"bw_unweighted": "betweenness\n(unweighted)", "total_syn": "synapse count",
            "in_deg": "in-degree", "out_deg": "out-degree",
            "influence": "adjusted\ninfluence", "traversal": "traversal\nmodel"}
    rows = {}
    for m in MODALITIES:
        df = pd.read_csv(os.path.join(ROOT, f"metric_matrix_{m}.csv"))
        mid = df[df.super_class == "central"].set_index("root_id")
        base = set(mid.nlargest(50, "bw_weighted").index)
        rows[m] = [len(base & set(mid.dropna(subset=[c]).nlargest(50, c).index))
                   for c in metrics]

    x = np.arange(len(metrics))
    w = 0.26
    fig, ax = plt.subplots(figsize=(9.5, 3.9))
    for i, m in enumerate(MODALITIES):
        off = (i - 1) * (w + 0.015)
        b = ax.bar(x + off, rows[m], w, color=COLOR[m], label=m, zorder=3)
        ax.bar_label(b, fontsize=7.5, padding=2, color=INK2)
    ax.set_xticks(x, [nice[c] for c in metrics])
    ax.set_ylabel("neurons shared with weighted-betweenness top 50")
    ax.set_ylim(0, 34)
    ax.grid(axis="y", zorder=0)
    ax.legend(frameon=False, ncols=3, loc="upper right")
    ax.set_title("Two metric families, and betweenness sits with the degree baselines",
                 pad=10)
    ax.text(0.02, 0.94, "chance overlap < 6 neurons in every pathway",
            transform=ax.transAxes, fontsize=7.5, color=INK2)
    save(fig, "fig2_metric_disagreement.png")


# ---------------------------------------------------------------- figure 3
def fig_deletion_damage():
    """Detour cost of deleting a neuron, candidates vs two control bands."""
    d = pd.read_csv(os.path.join(ROOT, "cross_modal_audit.csv"))
    groups = [("mid", "rank 1000+\ncontrol"), ("top50", "top-50\ncontrol"),
              ("candidate", "cross-modal\nfive")]
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.4), sharey=True)
    rng = np.random.default_rng(0)
    for ax, m in zip(axes, MODALITIES):
        sub = d[d.modality == m]
        for i, (g, _) in enumerate(groups):
            v = sub[sub.group == g].detour_pct.clip(lower=0.0008)
            ax.scatter(i + rng.uniform(-0.13, 0.13, len(v)), v, s=30,
                       color=COLOR[m], alpha=0.75, zorder=3,
                       edgecolors=SURFACE, linewidths=0.8)
        ax.set_yscale("log")
        ax.set_xticks(range(3), [lbl for _, lbl in groups], fontsize=8)
        ax.set_xlim(-0.5, 2.5)
        ax.set_title(m, color=COLOR[m])
        ax.grid(axis="y", zorder=0)
    axes[0].set_ylabel("% increase in sensory→motor\nroute length when deleted")
    fig.suptitle("The cross-modal five are ordinary: none exceeds its own pathway's "
                 "top-50 controls", fontsize=11, fontweight="bold", y=1.03)
    fig.text(0.5, -0.12, "Each point is one deleted neuron; values below 0.001% are drawn "
             "at the axis floor. The cross-modal five sit inside the top-50 control "
             "distribution in every pathway (z = −0.79 to +0.94) and cut no pairs, while "
             "several controls do.", ha="center", fontsize=7.5, color=INK2)
    save(fig, "fig3_deletion_damage.png")


# ---------------------------------------------------------------- figure 4
def fig_validated_composition():
    """What the null-surviving bottlenecks are: cell type and neuropil."""
    for m in MODALITIES:
        d = validated(m)
        keep = d[(d.q_z <= 0.05) & (d["rank"] <= 25)]
        fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.6))
        for ax, col, title in [(axes[0], "primary_type", "cell type"),
                               (axes[1], "neuropil", "neuropil")]:
            c = keep[col].astype(str).value_counts().head(10)
            b = ax.barh(c.index[::-1], c.values[::-1], color=COLOR[m], zorder=3,
                        height=0.72)
            ax.bar_label(b, fontsize=7.5, padding=2, color=INK2)
            ax.set_xlabel(f"count among {len(keep)} validated top-25 neurons")
            ax.set_title(title)
            ax.grid(axis="x", zorder=0)
            ax.set_xlim(0, max(c.values) * 1.18)
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        fig.suptitle(f"{m}: bottlenecks surviving the degree-preserving null",
                     fontsize=11, fontweight="bold", y=1.02)
        save(fig, f"fig4_validated_{m}.png")


# ---------------------------------------------------------------- figure 5
def fig_replication():
    """FAFB vs MCNS cell-type betweenness rank, one panel per pathway.

    Rank not raw betweenness: the two datasets differ in size and density, so the
    absolute scores are not on a common footing but the orderings are. Axes are
    inverted (rank 1 top-left) so "good in both" reads as the top-left corner.
    """
    d = pd.read_csv(os.path.join(ROOT, "dataset_comparison.csv"))
    stats = {"olfactory": (9, 0.52, 0.669), "mechanosensory": (12, 0.28, 0.710),
             "visual": (10, 2.22, 0.449)}
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 4.0))
    for ax, m in zip(axes, MODALITIES):
        s = d[d.modality == m]
        rest, hit = s[~s.in_both_top], s[s.in_both_top]
        ax.scatter(rest.fafb_rank, rest.mcns_rank, s=9, color=GRID, zorder=2,
                   label="other shared types")
        ax.scatter(hit.fafb_rank, hit.mcns_rank, s=40, color=COLOR[m], zorder=4,
                   edgecolors=SURFACE, linewidths=0.8, label="top-25 in both")
        for i, (_, r) in enumerate(hit.nsmallest(3, "fafb_rank").iterrows()):
            ax.annotate(r.primary_type, (r.fafb_rank, r.mcns_rank), fontsize=7,
                        color=INK2, xytext=(8, [7, -13, 7][i]),
                        textcoords="offset points")
        n_over, exp, rho = stats[m]
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.invert_yaxis()   # rank 1 at top; x stays ascending so rank 1 is at left
        ax.set_title(f"{m}  —  ρ = {rho:+.2f}", color=COLOR[m])
        ax.set_xlabel("FAFB v783 rank (female brain)")
        ax.grid(zorder=0)
        ax.text(0.97, 0.06, f"{n_over}/25 shared\n(chance {exp:.1f})",
                transform=ax.transAxes, fontsize=8, color=INK2, ha="right")
    axes[0].set_ylabel("MCNS v0.9 rank (male CNS)")
    axes[0].legend(frameon=False, fontsize=7.5, loc="lower left")
    fig.suptitle("Bottleneck cell types reproduce in a second connectome",
                 fontsize=11, fontweight="bold", y=1.03)
    fig.text(0.5, -0.07, "Each point is one cell type present in both datasets, ranked by "
             "max betweenness over its copies; both datasets computed under the same "
             "150-sampled-source protocol. Rank 1 is top-left; grey points are the remaining "
             "shared types.",
             ha="center", fontsize=7.5, color=INK2)
    save(fig, "fig5_replication.png")


def main():
    print("building poster figures...")
    fig_replication()
    fig_null_validation()
    fig_metric_disagreement()
    fig_deletion_damage()
    fig_validated_composition()


if __name__ == "__main__":
    main()
