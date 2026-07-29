"""Section 4.3 — the N=120 leaderboard is mostly sampling noise.

Recomputes, from published ARC-verified semi-private ARC-AGI-2 scores:
  - Wilson 95% confidence intervals per system (N=120 Bernoulli trials),
  - unpaired two-proportion z-tests for adjacent systems,
  - the number of tasks needed to resolve a frontier-scale gap at 80% power,
and renders fig_leaderboard_ci.png (a forest plot of scores with 95% CIs).

Scores are ARC-verified semi-private numbers (ARC Prize 2025 Technical Report /
public verified-leaderboard postings; verified frontier ~54%, Poetiq, Nov 2025).
Re-verify against arcprize.org/leaderboard at submission time. Do NOT substitute
third-party public/aggregator numbers (e.g. 77-92%): those are the very
public-vs-verified inflation this paper warns about.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

N = 120  # ARC-AGI-2 semi-private evaluation tasks

# (system, verified accuracy %) — top of the verified board, descending
SYSTEMS = [
    ("Poetiq (reported SOTA)",       54.0),
    ("Gemini 3 Pro (+refinement)",   54.0),
    ("Gemini 3 Deep Think",          45.0),
    ("Claude Opus 4.5 (Thinking)",   37.6),
    ("Kaggle 2025 winner (private)", 24.0),
]

def wilson(p_hat, n, z=1.96):
    p = p_hat / 100.0
    d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (100*(c-h), 100*(c+h))

def two_prop_p(p1, p2, n1=N, n2=N):
    a, b = p1/100.0, p2/100.0
    pool = (a*n1 + b*n2) / (n1 + n2)
    se = np.sqrt(pool*(1-pool)*(1/n1 + 1/n2))
    if se == 0: return 1.0
    z = abs(a - b) / se
    # two-sided normal p-value
    from math import erfc, sqrt
    return erfc(z/np.sqrt(2))

def tasks_for_power(diff_pts, center=50.0, power=0.80, alpha=0.05):
    """n per group to detect a diff_pts gap centered at `center`, two-sided."""
    from scipy.stats import norm
    p1 = (center - diff_pts/2)/100.0
    p2 = (center + diff_pts/2)/100.0
    za = norm.ppf(1 - alpha/2); zb = norm.ppf(power)
    num = (za + zb)**2 * (p1*(1-p1) + p2*(1-p2))
    return num / ((p2 - p1)**2)

if __name__ == "__main__":
    print(f"=== §4.3 Leaderboard statistics (N={N}) ===\n")
    print(f"{'System':32s} {'score':>6s}  95% Wilson CI")
    for name, s in SYSTEMS:
        lo, hi = wilson(s, N)
        print(f"{name:32s} {s:5.1f}%  [{lo:.1f}, {hi:.1f}]")

    print("\nAdjacent two-proportion tests (unpaired, conservative):")
    for (n1, s1), (n2, s2) in zip(SYSTEMS, SYSTEMS[1:]):
        p = two_prop_p(s1, s2)
        sig = "" if p >= 0.05 else "  *"
        print(f"  {s1:.1f}% vs {s2:.1f}%  ->  p = {p:.3f}{sig}")
    p_top = two_prop_p(54.0, 45.0)
    print(f"\n  Headline 'SOTA gap' 54.0% vs 45.0%:  p = {p_top:.2f}  (not significant)")

    print("\nPower: tasks/system to resolve a gap near the 50% frontier at 80% power:")
    for d in (5, 3, 2):
        print(f"  {d}-point gap -> n = {tasks_for_power(d):,.0f} tasks  (have {N})")

    # ---- figure: forest plot ----
    fig, ax = plt.subplots(figsize=(7.4, 3.5))
    ys = np.arange(len(SYSTEMS))[::-1]
    for y, (name, s) in zip(ys, SYSTEMS):
        lo, hi = wilson(s, N)
        ax.plot([lo, hi], [y, y], color="#3a6ea5", lw=3, solid_capstyle="round", zorder=2)
        ax.plot(s, y, "o", color="#c0392b", ms=7, zorder=3)
        ax.annotate(f"{s:.1f}%", (s, y), textcoords="offset points", xytext=(0, 8),
                    ha="center", fontsize=9, fontweight="bold")
    # shade the region shared by the top-two contenders
    lo1, hi1 = wilson(54.0, N)
    ax.axvspan(lo1, hi1, color="#f4d03f", alpha=0.15, zorder=0)
    ax.set_yticks(ys); ax.set_yticklabels([n for n, _ in SYSTEMS], fontsize=9)
    ax.set_xlabel("ARC-AGI-2 accuracy (%) — 95% Wilson CI on N=120 tasks", fontsize=9)
    ax.set_title("Every leaderboard number is ±~9 points; the SOTA “lead” is within noise",
                 fontsize=10.5, fontweight="bold")
    ax.text(0.985, 0.06, f"top-two 9-pt gap: p={p_top:.2f} (n.s.)", transform=ax.transAxes,
            ha="right", fontsize=8.5, color="#7a6000",
            bbox=dict(boxstyle="round,pad=0.3", fc="#fdf6d8", ec="#e0c85a"))
    ax.set_xlim(10, 70); ax.grid(axis="x", ls=":", alpha=0.5)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig("fig_leaderboard_ci.png", dpi=150)
    print("\nwrote fig_leaderboard_ci.png")
