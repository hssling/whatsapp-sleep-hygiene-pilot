"""Figures 1-3: 600 dpi RGB TIFF (LZW) and JPEG. Each figure checks its own layout (no clipped or
overlapping text) before it is saved."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch
from PIL import Image

from .tables import sensitivity_rows

NAVY, RED, BLUE, GREY = "#1f3b57", "#b03a2e", "#1f618d", "#6b6b6b"
SEED = 20260930


def _save(fig, outdir, stem):
    outdir.mkdir(parents=True, exist_ok=True)
    png = outdir / f"{stem}.png"
    fig.savefig(png, dpi=600, facecolor="white")
    plt.close(fig)
    im = Image.open(png).convert("RGB")
    im.save(outdir / f"{stem}.jpg", quality=95, dpi=(600, 600))
    im.save(outdir / f"{stem}.tif", compression="tiff_lzw", dpi=(600, 600))
    png.unlink()


def check_layout(fig, name):
    """Every visible text lies inside the canvas; panel letters/titles, tick labels, annotations and
    legend entries do not collide."""
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    W, H = fig.canvas.get_width_height()
    hidden = set()
    for ax in fig.axes:
        for axis, (lo, hi) in ((ax.xaxis, sorted(ax.get_xlim())), (ax.yaxis, sorted(ax.get_ylim()))):
            for tick in axis.get_major_ticks():
                if not lo - 1e-9 <= tick.get_loc() <= hi + 1e-9:
                    hidden.update({id(tick.label1), id(tick.label2)})
    texts = [t for t in fig.findobj(matplotlib.text.Text)
             if t.get_visible() and t.get_text().strip() and id(t) not in hidden]
    for t in texts:
        bb = t.get_window_extent(rend)
        assert bb.x0 >= -1 and bb.x1 <= W + 1 and bb.y0 >= -1 and bb.y1 <= H + 1, f"{name}: clipped {t.get_text()!r}"
    heads = [a.title for a in fig.axes if a.get_title()]
    heads += [t for t in texts if len(t.get_text()) == 1 and t.get_fontweight() == "bold"]
    boxes = [(h.get_text(), h.get_window_extent(rend)) for h in heads]
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            assert not boxes[i][1].overlaps(boxes[j][1]), f"{name}: {boxes[i][0]!r} overlaps {boxes[j][0]!r}"
    for ax in fig.axes:
        for labels in (ax.get_xticklabels(), ax.get_yticklabels()):
            bb = [(t.get_text(), t.get_window_extent(rend)) for t in labels
                  if t.get_visible() and t.get_text().strip() and id(t) not in hidden]
            for i in range(len(bb)):
                for j in range(i + 1, len(bb)):
                    assert not bb[i][1].overlaps(bb[j][1]), f"{name}: tick labels {bb[i][0]!r}/{bb[j][0]!r} overlap"
        tb = [(t.get_text(), t.get_window_extent(rend)) for t in ax.texts if t.get_visible() and t.get_text().strip()]
        for i in range(len(tb)):
            for j in range(i + 1, len(tb)):
                assert not tb[i][1].overlaps(tb[j][1]), f"{name}: annotations {tb[i][0]!r}/{tb[j][0]!r} overlap"
        leg = ax.get_legend()
        if leg is not None:
            lb = leg.get_window_extent(rend)
            own = {id(t) for t in leg.findobj(matplotlib.text.Text)}
            for t in texts:
                if id(t) not in own:
                    assert not lb.overlaps(t.get_window_extent(rend)), f"{name}: legend covers {t.get_text()!r}"
            labels = [t.get_text() for t in leg.get_texts()]
            assert len(labels) == len(set(labels)), f"{name}: duplicate legend entries"


def _panel(ax, letter, x=-0.14):
    ax.text(x, 1.06, letter, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom")


# ------------------------------------------------------------------------------------------ Figure 1
def figure1(R, outdir):
    f = R["flow"]
    W, BOX_H, GAP = 10.0, 1.05, 0.62
    lx, rx, bw = 0.4, 5.4, 4.2
    rows = [
        [(1.9, 6.2, f"Third-year MBBS students in the baseline survey\nn = {f['third_year']}", NAVY)],
        [(lx, bw, f"Baseline poor sleepers (PSQI > 5)\ninvited: n = {f['third_year_poor']}", RED),
         (rx, bw, f"Baseline good sleepers (PSQI ≤ 5)\nnot invited: n = {f['third_year_good']}", BLUE)],
        [(lx, bw, f"Joined the programme\nn = {f['joined_poor']}", RED),
         (rx, bw, f"Asked to join and were allowed\nn = {f['joined_good']}", BLUE)],
        [(lx, bw, f"Follow-up PSQI and ESS analysed\nn = {f['poor_analysed']} (primary analysis)", RED),
         (rx, bw, f"Follow-up PSQI and ESS analysed\nn = {f['good_analysed']} (received the programme)", BLUE)],
    ]
    side = {1: [(lx, f"Did not join: n = {f['poor_not_joined']}")],
            2: [(lx, f"No follow-up form: n = {f['poor_lost']}"),
                (rx, f"No follow-up form: n = {f['good_lost']}\nConsent item answered 'No': n = {f['good_excluded_consent']}")]}
    fig, ax = plt.subplots(figsize=(6.5, 6.3))
    y, placed = 0.0, []
    for i, row in enumerate(rows):
        y -= BOX_H
        for x, w_, text, col in row:
            ax.add_patch(FancyBboxPatch((x, y), w_, BOX_H, boxstyle="round,pad=0.02,rounding_size=0.08",
                                        fc="white", ec=col, lw=1.2))
            placed.append((x, y, w_, ax.text(x + w_ / 2, y + BOX_H / 2, text, ha="center", va="center", fontsize=8.2)))
        if i < len(rows) - 1:
            top = y
            y -= GAP
            for x in (lx, rx):
                ax.annotate("", xy=(x + bw / 2, y), xytext=(W / 2 if i == 0 else x + bw / 2, top),
                            arrowprops=dict(arrowstyle="-|>", color=GREY, lw=0.9))
            for x, t in side.get(i, []):
                ax.text(x + bw / 2 + 0.1, top - GAP / 2, t, ha="left", va="center", fontsize=7.0, color=GREY)
    y -= 0.5
    ax.text(W / 2, y,
            f"Education session (13 July 2026): attended by all {f['group_members']} members of the programme group; "
            f"{f['submitted_any']} submitted a diary entry or\nfollow-up form, of whom {f['linked']} were linked to a "
            f"baseline record ({f['unlinked']} registration numbers matched more than one student).\n"
            "Baseline survey: 26-27 May 2026. Programme: 13 July to 10 August 2026. Follow-up forms: 13-23 August 2026.",
            ha="center", va="top", fontsize=6.6, color=GREY)
    bottom = y - 0.75
    ax.set_xlim(0, W)
    ax.set_ylim(bottom, 0.2)
    ax.axis("off")
    for a in range(len(placed)):
        for b in range(a + 1, len(placed)):
            xa, ya, wa, _ = placed[a]
            xb, yb, wb, _ = placed[b]
            assert not (xa < xb + wb and xb < xa + wa and ya < yb + BOX_H and yb < ya + BOX_H), "boxes overlap"
    fig.tight_layout()
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    for x, yy, w_, t in placed:
        tb = t.get_window_extent(rend)
        (bx0, by0), (bx1, by1) = ax.transData.transform([(x, yy), (x + w_, yy + BOX_H)])
        pad = 0.04 * (bx1 - bx0)
        assert bx0 + pad <= tb.x0 and tb.x1 <= bx1 - pad and by0 <= tb.y0 and tb.y1 <= by1, t.get_text()
    check_layout(fig, "Figure 1")
    _save(fig, outdir, "Figure 1")


# ------------------------------------------------------------------------------------------ Figure 2
def _duration_panel(ax, g, col, light, lab):
    bins = [0, 5.25, 5.75, 6.25, 6.75, 7.25, 7.75, 8.25, 12]
    labels = ["<5.5", "5.5", "6", "6.5", "7", "7.5", "8", ">8"]
    b = np.histogram(g["b_sleep_duration_hours"].astype(float), bins=bins)[0]
    f = np.histogram(g["f_sleep_duration_hours"].astype(float), bins=bins)[0]
    x = np.arange(len(labels))
    ax.bar(x - 0.2, b, 0.4, color=light, edgecolor=col, lw=0.8, label="Baseline")
    ax.bar(x + 0.2, f, 0.4, color=col, edgecolor=col, lw=0.8, label="Follow-up")
    ax.axvline(6, color="black", ls=":", lw=1)
    ax.text(6.05, 13.6, "taught target", fontsize=7, va="top", ha="left")
    ax.set_xticks(x, labels, fontsize=7.5)
    ax.set_xlabel("Reported hours of sleep per night", fontsize=8.5)
    ax.set_title(f"Sleep duration, {lab} (n = {len(g)})", fontsize=8.5)
    ax.yaxis.get_major_locator().set_params(integer=True)
    ax.spines[["top", "right"]].set_visible(False)


def figure2(w, outdir):
    poor = w[(w["group"] == "poor") & w["fu_analysed"]]
    good = w[(w["group"] == "good") & w["fu_analysed"]]
    fig = plt.figure(figsize=(6.8, 7.0))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.15, 1], hspace=0.6, wspace=0.18)
    axes = [fig.add_subplot(gs[0, 0])]
    axes.append(fig.add_subplot(gs[0, 1], sharey=axes[0]))
    rng = np.random.default_rng(SEED)
    for k, (ax, lab, g, col) in enumerate(zip(axes, ["poor sleepers", "good sleepers"], [poor, good], [RED, BLUE])):
        for r in g.itertuples():
            j = rng.uniform(-0.18, 0.18, 2)
            ax.plot([j[0] * 0.3, 1 + j[1] * 0.3], [max(r.b_PSQI_global + j[0], 0), max(r.f_PSQI_global + j[1], 0)],
                    color=col, alpha=0.35, lw=0.8)
        for t, cn in enumerate(["b_PSQI_global", "f_PSQI_global"]):
            v = g[cn].astype(float)
            ax.errorbar(t, v.mean(), yerr=1.96 * v.std(ddof=1) / np.sqrt(len(v)), fmt="o", color="black", ms=5,
                        capsize=4, lw=1.2, zorder=5)
        ax.axhline(5.5, ls="--", color=GREY, lw=0.8)
        ax.set_xticks([0, 1], ["Baseline\n(late May)", "Follow-up\n(August)"], fontsize=8)
        ax.set_xlim(-0.4, 1.4)
        ax.set_title(f"PSQI, baseline {lab} (n = {len(g)})", fontsize=8.5)
        ax.spines[["top", "right"]].set_visible(False)
        _panel(ax, "AB"[k])
    axes[1].tick_params(labelleft=False)
    axes[0].set_ylabel("PSQI global score (0-21; higher = worse)", fontsize=8.5)
    axes[0].set_ylim(-0.3, 14)
    axes[0].set_yticks(range(0, 15, 2))
    axc = fig.add_subplot(gs[1, 0])
    axd = fig.add_subplot(gs[1, 1], sharey=axc)
    axc.set_ylim(0, 14)
    _duration_panel(axc, poor, RED, "#f2c4bf", "poor sleepers")
    _duration_panel(axd, good, BLUE, "#c9dcea", "good sleepers")
    axc.set_ylabel("Students", fontsize=8.5)
    axd.tick_params(labelleft=False)
    axc.legend(fontsize=7.5, frameon=False, loc="upper left")
    axd.legend(fontsize=7.5, frameon=False, loc="upper left")
    _panel(axc, "C")
    _panel(axd, "D")
    check_layout(fig, "Figure 2")
    _save(fig, outdir, "Figure 2")


# ------------------------------------------------------------------------------------------ Figure 3
def figure3(R, outdir):
    fig = plt.figure(figsize=(6.8, 8.6))
    gs = fig.add_gridspec(2, 1, height_ratios=[1, 1.45], hspace=0.36, left=0.47, right=0.97, top=0.95, bottom=0.06)
    ax = fig.add_subplot(gs[0])
    rt = sorted(R["rtm"], key=lambda x: x["rho"])
    rho = [x["rho"] for x in rt]
    ax.axvspan(0.68, 0.87, color="#e8e8e8", lw=0)
    for key, col, mk, lab in (("poor", RED, "o", "Poor sleepers"), ("good", BLUE, "s", "Good sleepers")):
        ax.fill_between(rho, [x[f"adjusted_{key}_ci"][0] for x in rt], [x[f"adjusted_{key}_ci"][1] for x in rt],
                        color=col, alpha=0.15, lw=0)
        ax.plot(rho, [x[f"adjusted_{key}"] for x in rt], color=col, lw=1.6, marker=mk, ms=3.2,
                label=f"{lab} (95% CI band)")
    ax.axhline(0, color="black", lw=0.7)
    ax.text(0.775, -5.3, "external\nretest\nestimates", fontsize=6.4, ha="center", va="bottom", color="#404040")
    ax.set_ylim(-5.6, 1.2)
    ax.set_xlim(-0.02, 0.92)
    ax.set_title("Allowing for regression to the mean", fontsize=8.5)
    ax.set_xlabel("Assumed test-retest correlation of the PSQI (r)", fontsize=9)
    ax.set_ylabel("Adjusted change in PSQI", fontsize=9)
    ax.legend(fontsize=6.8, frameon=False, loc="upper right", bbox_to_anchor=(0.62, 1.0))
    ax.spines[["top", "right"]].set_visible(False)
    _panel(ax, "A", x=-0.11)
    axb = fig.add_subplot(gs[1])
    rows = sensitivity_rows(R)
    groups = []
    for g, *_ in rows:
        if g not in groups:
            groups.append(g)
    items, labels = [], []
    for g in groups:
        items.append(None)
        labels.append(g)
        for r in rows:
            if r[0] == g:
                items.append(r)
                labels.append("   " + r[1])
    n_ = len(items)
    for k, it in enumerate(items):
        if it is None:
            continue
        yy = n_ - 1 - k
        g, lab, n, e, lo, hi, _ = it
        col = RED if g == "Primary analysis" else BLUE if g == "Reference" else GREY if lab.startswith("Mixed") else NAVY
        axb.plot([lo, hi], [yy, yy], color=col, lw=1.2)
        axb.plot(e, yy, "s", color=col, ms=4.5, mfc="white" if lab.startswith("Mixed") else col)
    axb.set_yticks(range(n_), labels[::-1], fontsize=6.6)
    for tl, it in zip(axb.get_yticklabels(), items[::-1]):
        if it is None:
            tl.set_fontweight("bold")
    axb.axvline(0, color="black", lw=0.7)
    axb.axvline(R["primary"]["mean_diff"], color=GREY, lw=0.8, ls="--")
    lo_all = min(r[4] for r in rows)
    hi_all = max(r[5] for r in rows)
    axb.set_xlim(np.floor(lo_all) - 0.5, np.ceil(hi_all) + 0.5)
    axb.set_title("Change in PSQI under alternative analyses", fontsize=8.5)
    axb.set_xlabel("Change in PSQI global score (95% CI)", fontsize=9)
    axb.spines[["top", "right"]].set_visible(False)
    _panel(axb, "B", x=-0.86)
    pos = ax.get_position()
    ax.set_position([0.12, pos.y0, 0.85, pos.height])
    check_layout(fig, "Figure 3")
    _save(fig, outdir, "Figure 3")
