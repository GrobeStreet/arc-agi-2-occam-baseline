"""Figures from the enriched calibration/selection corpus (ablate_v2 outputs).

fig1_calibration.png : P(a k-demo-consistent program generalizes to the next demo)
                       vs k, with 95% Wilson CIs, against the solver's implicit
                       "it fits the demos" ~100% confidence. ARC-AGI-2's mean of
                       2.99 demonstrations is marked.
fig_selection.png    : accuracy on AMBIGUOUS (task,k) cells by selection rule —
                       random / consensus-vote / shortest-MDL (Occam) / oracle —
                       with 95% Wilson CIs. Occam matches the oracle ceiling.
"""
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

def wilson(k, n, z=1.96):
    if n == 0: return (0, 0, 0)
    p = k / n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (100*p, 100*(c-h), 100*(c+h))

pp = pd.read_parquet("ablate_prog_training.parquet")
cc = pd.read_parquet("ablate_cell_training.parquet")

# ---------- fig1: calibration curve ----------
ks, mids, los, his = [], [], [], []
for k in sorted(pp.k.unique()):
    s = pp[pp.k == k]
    if len(s) >= 20:
        m, lo, hi = wilson(s.correct.sum(), len(s))
        ks.append(k); mids.append(m); los.append(lo); his.append(hi)
ks = np.array(ks); mids = np.array(mids)
yerr = np.vstack([mids - np.array(los), np.array(his) - mids])

fig, ax = plt.subplots(figsize=(7.2, 4.0))
ax.axhline(100, ls="--", color="#888", lw=1.3, label="solver's implicit confidence (“it fits the demos”)")
ax.fill_between(ks, mids, 100, color="#c0392b", alpha=0.10)
ax.errorbar(ks, mids, yerr=yerr, fmt="o-", color="#c0392b", lw=2.2, ms=7,
            capsize=4, label="actual generalization rate (95% CI)", zorder=3)
for k, m in zip(ks, mids):
    ax.annotate(f"{m:.0f}%", (k, m), textcoords="offset points", xytext=(9, -4),
                fontsize=9.5, fontweight="bold", color="#c0392b")
ax.axvline(2.99, ls=":", color="#2c5aa0", lw=1.4)
ax.text(2.96, 8, "ARC-AGI-2 mean = 2.99 demos", rotation=90, va="bottom",
        ha="right", fontsize=8.5, color="#2c5aa0")
ax.set_xlabel("# demonstrations the program was required to fit (k)", fontsize=9.5)
ax.set_ylabel("generalizes to held-out demonstration (%)", fontsize=9.5)
ax.set_title('“Fits the demonstrations” is a miscalibrated confidence signal',
             fontsize=11, fontweight="bold")
ax.set_ylim(0, 108); ax.set_xticks(ks); ax.set_xlim(ks.min()-0.3, ks.max()+0.5)
ax.grid(axis="y", ls=":", alpha=0.5); ax.spines[["top", "right"]].set_visible(False)
ax.legend(loc="lower right", fontsize=8.5, framealpha=0.95)
fig.tight_layout(); fig.savefig("fig1_calibration.png", dpi=150)
print("wrote fig1_calibration.png  (k, rate):", list(zip(ks.tolist(), [round(m,1) for m in mids])))

# ---------- fig_selection: selection rules on ambiguous cells ----------
amb = cc[cc.ambiguous == 1]
n = len(amb)
rules = [
    ("Random\nconsistent program", amb.random_rate.mean()*100, None, None, "#9aa7b4"),
    ("Consensus\nvote",            *wilson(amb.consensus_correct.sum(), n), "#5a7fa5"),
    ("Shortest — MDL\n(Occam)",    *wilson(amb.shortest_correct.sum(), n), "#c0392b"),
    ("Oracle ceiling\n(any correct)", *wilson(amb.any_correct.sum(), n), "#2e7d32"),
]
fig, ax = plt.subplots(figsize=(7.2, 3.9))
xs = np.arange(len(rules))
for x, r in zip(xs, rules):
    label, m = r[0], r[1]
    color = r[-1]
    if r[2] is None:  # random: mean over programs, no single-count CI
        ax.bar(x, m, color=color, width=0.62, zorder=2)
    else:
        lo, hi = r[2], r[3]
        ax.bar(x, m, color=color, width=0.62, zorder=2,
               yerr=[[m-lo], [hi-m]], capsize=5, ecolor="#333")
    ax.annotate(f"{m:.1f}%", (x, m), textcoords="offset points", xytext=(0, 6),
                ha="center", fontsize=10, fontweight="bold")
ax.axhline(rules[-1][1], ls="--", color="#2e7d32", lw=1.2, alpha=0.7)
ax.set_xticks(xs); ax.set_xticklabels([r[0] for r in rules], fontsize=9)
ax.set_ylabel("accuracy on ambiguous cells (%)", fontsize=9.5)
ax.set_title(f"Description-length (Occam) selection matches the oracle  (n={n} ambiguous cells)",
             fontsize=10.5, fontweight="bold")
ax.set_ylim(0, max(r[1] for r in rules) + 16)
ax.grid(axis="y", ls=":", alpha=0.5); ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig("fig_selection.png", dpi=150)
print(f"wrote fig_selection.png  (n_ambiguous={n})")
print("  random %.1f  consensus %.1f  Occam %.1f  oracle %.1f" % (
    amb.random_rate.mean()*100, amb.consensus_correct.mean()*100,
    amb.shortest_correct.mean()*100, amb.any_correct.mean()*100))
