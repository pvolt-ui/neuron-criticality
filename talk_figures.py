#!/usr/bin/env python
"""talk_figures.py -- the three figures for the 4-minute symposium talk.

  talk_fig_bottlenecks.png   per pathway: the validated bottleneck cell types (text) +
                             deletion damage (top-50 vs rank-1000+) -- "real, but redundant"
  talk_fig_null.png          Null B z per rank with the selection-control floor drawn in
  talk_fig_replication.png   FAFB vs MCNS top-25 overlap, betweenness vs degree baseline
Colors match the poster set (blue / orange / green).
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.abspath(__file__))
P = ["olfactory", "mechanosensory", "visual"]
COL = {"olfactory": "#2F6FDB", "mechanosensory": "#F07A2D", "visual": "#1FA97C"}
LABEL = {"olfactory": "olfactory\nORN → DN", "mechanosensory": "mechanosensory\nJO → DN",
         "visual": "visual\nlamina/medulla → DN"}
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False})


def save(fig, name):
    fig.savefig(os.path.join(ROOT, name), dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", name)


NAVYF, LIGHTF, DIMF = "#16233A", "#F5F3EE", "#B9BDC9"


def fig_schematic():
    """Wide navy strip for slide 2: what a pathway graph is, and what betweenness ranks."""
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Circle
    fig, ax = plt.subplots(figsize=(12.4, 2.45))
    fig.patch.set_facecolor(NAVYF); ax.set_facecolor(NAVYF)
    ax.set_xlim(0, 100); ax.set_ylim(0, 30); ax.axis("off")

    def arrow(x1, y1, x2, y2, c=DIMF, lw=1.6, alpha=1.0, ms=11):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=ms,
                                     color=c, lw=lw, alpha=alpha, shrinkA=0, shrinkB=0))

    # --- 1. sensory sources -------------------------------------------------
    for m, lab, y in [("olfactory", "ORNs", 23.2), ("mechanosensory", "JO neurons", 14.5),
                      ("visual", "lamina / medulla", 5.8)]:
        for k in range(3):
            ax.add_patch(Circle((6.5 + k * 2.7, y), 1.0, color=COL[m], zorder=3))
        ax.text(3.8, y + 2.7, m, color=COL[m], fontsize=10.5, fontweight="bold", ha="left")
        ax.text(3.8, y - 3.1, lab, color=DIMF, fontsize=9, ha="left")
        arrow(13.2, y, 30.0, 14.5 + (y - 14.5) * 0.35, c=COL[m], lw=2.0, alpha=.85)

    # --- 2. interneuron zone (the pathway subgraph) -------------------------
    ax.add_patch(FancyBboxPatch((31, 4.0), 27, 19.5, boxstyle="round,pad=0.4,rounding_size=1.2",
                                fc="#22334F", ec="#3C5480", lw=1.4, zorder=1))
    ax.text(33.2, 5.6, "central interneurons", color="#9FB0CC", fontsize=10, ha="left", zorder=6)
    rng = np.random.default_rng(11)
    pts = np.column_stack([rng.uniform(34.5, 55, 22), rng.uniform(9.5, 21, 22)])
    for (px, py) in pts:
        ax.add_patch(Circle((px, py), 0.7, color="#5C7195", zorder=3))
    for i in range(0, 20, 2):
        arrow(*pts[i], *pts[i + 1], c="#3F5578", lw=0.8, ms=7)
    ax.add_patch(Circle((44.5, 14.5), 2.0, color="#F2C14E", zorder=5))
    for dx, dy in [(-7.5, 4.5), (-8.5, -2), (-6.5, -4.5), (7.5, 5), (8.5, 0), (6.5, -4.5)]:
        arrow(44.5 + dx * .5, 14.5 + dy * .5, 44.5 + dx, 14.5 + dy, c="#F2C14E", lw=1.6, alpha=.95, ms=9)
    ax.annotate("chokepoint — most of the strong routes pass through here",
                xy=(44.5, 17.0), xytext=(44.5, 27.6), color="#F2C14E", fontsize=10.5,
                fontweight="bold", ha="center", va="center",
                arrowprops=dict(arrowstyle="-|>", color="#F2C14E", lw=1.2, mutation_scale=10))

    # --- 3. descending -> behaviour ----------------------------------------
    ax.add_patch(FancyBboxPatch((66, 7.5), 12, 14, boxstyle="round,pad=0.4,rounding_size=1.2",
                                fc="#22334F", ec="#3C5480", lw=1.4, zorder=1))
    for y in (18.5, 14.5, 10.5):
        ax.add_patch(Circle((72, y), 1.1, color="#9AA7BD", zorder=3))
        arrow(58.6, 14.5 + (y - 14.5) * .45, 65.4, y, c=DIMF, lw=1.3, alpha=.75)
    ax.text(72, 23.6, "descending neurons", color=LIGHTF, fontsize=11,
            fontweight="bold", ha="center")
    ax.text(72, 4.6, "(motor command)", color=DIMF, fontsize=9.5, ha="center")
    arrow(78.6, 14.5, 87, 14.5, c=DIMF, lw=2.0)
    ax.text(93.8, 14.5, "behaviour", color=LIGHTF, fontsize=12, fontweight="bold",
            ha="center", va="center")

    # --- hop annotations ----------------------------------------------------
    for x0, x1 in [(14, 29.5), (59, 65)]:
        ax.plot([x0, x1], [1.9, 1.9], color="#6E7C96", lw=1.0)
        ax.text((x0 + x1) / 2, 0.4, "\u2264 2 synapses", color="#8794AC", fontsize=9,
                ha="center", va="bottom")
    fig.savefig(os.path.join(ROOT, "talk_fig_schematic.png"), dpi=200,
                bbox_inches="tight", facecolor=NAVYF)
    plt.close(fig)
    print("saved talk_fig_schematic.png")


def fig_null():
    # control floors: max z seen in any structureless pseudo-real graph
    ctl = {}
    for m in P:
        fp = os.path.join(ROOT, f"nullB_selection_control_{m}.csv")
        ctl[m] = pd.read_csv(fp) if os.path.exists(fp) else None
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharey=True)
    for ax, m in zip(axes, P):
        d = pd.read_csv(os.path.join(ROOT, f"null_degree_{m}.csv"))
        z = d.z.replace(np.inf, 300).clip(lower=0.05)
        ok = d.q_z <= 0.05
        ax.scatter(d["rank"][ok], z[ok], s=42, color=COL[m], zorder=3, label="beats degree null (FDR q≤.05)")
        ax.scatter(d["rank"][~ok], z[~ok], s=42, facecolors="none", edgecolors="#C0392B", lw=1.6, zorder=3, label="fails")
        ax.set_yscale("log"); ax.set_ylim(0.04, 400); ax.set_xlim(0, 51)
        ax.axvline(25.5, color="#888", ls="--", lw=1)
        if ctl[m] is not None:
            floor = ctl[m].max_z.max()
            ax.axhline(floor, color="#333", lw=1.8, ls=":")
            ax.text(50, floor * 1.25, f"selection-only ceiling (z={floor:.0f})\n"
                    f"{ctl[m].surv_qz_top50.mean():.0f}/50 'survive' in a shuffled graph",
                    ha="right", va="bottom", fontsize=9.5, color="#333")
            above = int((d.z > floor).sum())
            ttl = f"{m}\n{int(ok.sum())}/50 pass FDR · {above}/50 above selection ceiling"
        else:
            ttl = f"{m}\n{int(ok.sum())}/50 pass FDR · (control not run)"
        ax.set_title(ttl, color=COL[m], fontsize=11.5, fontweight="bold")
        ax.set_xlabel("betweenness rank")
        ax.grid(axis="y", alpha=.3)
    axes[0].set_ylabel("z vs degree-preserving null")
    axes[0].legend(loc="lower left", fontsize=9, frameon=False)
    fig.suptitle("A few neurons per pathway are bottlenecks by position, not degree — most FDR 'survivors' are selection",
                 fontsize=13, fontweight="bold", y=1.06)
    save(fig, "talk_fig_null.png")


def fig_replication():
    rows = []
    for line in open(os.path.join(ROOT, "replication_specificity.txt")):
        if line.strip().startswith(("betweenness", "total_syn")):
            lab = "betweenness" if "betweenness" in line else "degree (total syn)"
            hit = int(line.split("overlap")[1].split("(")[0])
            exp = float(line.split("exp ")[1].split(",")[0])
            rows.append((lab, hit, exp))
    cur = None; data = {}
    for line in open(os.path.join(ROOT, "replication_specificity.txt")):
        if line.startswith("---"): cur = line.strip("- \n")
        elif cur and line.strip().startswith(("betweenness", "total_syn")):
            lab = "betweenness" if "betweenness" in line.split()[0] else "degree"
            hit = int(line.split("overlap")[1].split("(")[0]); exp = float(line.split("exp ")[1].split(",")[0])
            rho = float(line.split("rho all")[1].split()[0])
            data.setdefault(cur, {})[lab] = (hit, exp, rho)
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    x = np.arange(len(P)); wd = 0.36
    for i, m in enumerate(P):
        b = data[m]["betweenness"]; g = data[m]["degree"]
        ax.bar(i - wd/2, b[0], wd, color=COL[m], label="betweenness" if i == 0 else None)
        ax.bar(i + wd/2, g[0], wd, color=COL[m], alpha=.35, hatch="//", label="degree baseline" if i == 0 else None)
        ax.plot([i - wd, i + wd], [b[1], b[1]], color="k", lw=1.5)
        ax.text(i - wd/2, b[0] + .5, f"{b[0]}\nρ={b[2]:.2f}", ha="center", fontsize=10)
        ax.text(i + wd/2, g[0] + .5, f"{g[0]}\nρ={g[2]:.2f}", ha="center", fontsize=10, color="#555")
    ax.plot([], [], color="k", lw=1.5, label="chance (hypergeometric)")
    ax.set_xticks(x); ax.set_xticklabels([LABEL[m] for m in P])
    ax.set_ylabel("top-25 cell types shared, FAFB ∩ MCNS"); ax.set_ylim(0, 25)
    ax.legend(frameon=False, fontsize=10, loc="upper left")
    ax.set_title("Bottleneck cell types replicate in a second animal —\nbut so does degree, even better",
                 fontsize=12.5, fontweight="bold")
    save(fig, "talk_fig_replication.png")


def fig_bottlenecks():
    audit = pd.read_csv(os.path.join(ROOT, "cross_modal_audit.csv"))
    mc = pd.read_csv(os.path.join(ROOT, "mcns", "robustness.csv"))
    rng = np.random.default_rng(0)
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    wd = 0.26
    for i, m in enumerate(P):
        a = audit[audit.modality == m]
        top = a[a.group.isin(["top50", "candidate"])].detour_pct.to_numpy()
        mid = a[a.group == "mid"].detour_pct.to_numpy()
        r = mc[(mc.modality == m) & (mc.band == "top50")].detour_pct.to_numpy()
        groups = [(i - wd, top, COL[m], 1.0, None, "FAFB: delete one top-50 bottleneck"),
                  (i, r, COL[m], 0.45, "//", "MaleCNS: same test, 2nd animal"),
                  (i + wd, mid, "#999999", 1.0, None, "FAFB: delete a rank-1000+ neuron")]
        for x, v, c, al, ht, lab in groups:
            if len(v) == 0:
                ax.text(x, 0.15, "not\nrun", ha="center", fontsize=8.5, color="#777"); continue
            ax.bar(x, v.mean(), wd * 0.9, color=c, alpha=al, hatch=ht, label=lab if i == 0 else None, zorder=2)
            ax.scatter(x + rng.uniform(-wd * 0.3, wd * 0.3, len(v)), v, s=12, color="k", alpha=.6, zorder=3)
        ncut = int((a[a.group == "top50"].cut_pairs > 0).sum())
        ax.text(i - wd, top.max() + .25, f"max {top.max():.1f}%", ha="center", fontsize=9)
        ax.text(i, -0.55, f"{ncut}/12 top-50 controls sever\na single sensory source", ha="center",
                fontsize=8.5, color="#555")
    ax.set_xticks(range(len(P))); ax.set_xticklabels([LABEL[m] for m in P]); ax.tick_params(axis="x", pad=22)
    ax.set_ylabel("route lengthening after one deletion (%)"); ax.set_ylim(0, 5.2)
    ax.legend(frameon=False, fontsize=9.5, loc="upper left")
    ax.set_title("Deleting any single bottleneck lengthens strong sensory→motor routes by ~0.3–0.6 % on average\n(max 4.5 %); no cross-modal candidate disconnects a single pair",
                 fontsize=11.5, fontweight="bold")
    save(fig, "talk_fig_deletion.png")


if __name__ == "__main__":
    fig_schematic(); fig_null(); fig_replication()
    try:
        fig_bottlenecks()
    except Exception as e:  # deletion audit for visual may still be running
        print("deletion figure skipped:", e)
