"""Core experiment (v2): generalization reliability of a demonstration-consistent
program vs. how many demonstrations (k) it had to fit, PLUS the selection problem.
For each task with demos d_0..d_{D-1} and each k in 1..D-1:
  - build programs consistent with d_0..d_{k-1}
  - each predicts the held-out NEXT demo d_k; we record the prediction identity so we
    can measure ambiguity (distinct predictions), and test selection rules
    (random / shortest-MDL / consensus-vote) and whether consensus is calibrated."""
import json, glob, os, sys, numpy as np, pandas as pd
from dsl import build_programs, passes_demos, complexity

SPLIT = sys.argv[1] if len(sys.argv) > 1 else "training"
ROOT = "/home/claude/ARC-AGI-2/data/" + SPLIT
files = sorted(glob.glob(ROOT + "/*.json"))

prog_rows = []   # (task,k,program): k-consistent + correct-on-next
cell_rows = []   # (task,k): ambiguity + selection outcomes + consensus confidence
for f in files:
    tid = os.path.basename(f)[:-5]
    t = json.load(open(f))
    demos = [(np.array(p["input"]), np.array(p["output"])) for p in t["train"]]
    D = len(demos)
    for k in range(1, D):
        fit = demos[:k]; nxt_in, nxt_out = demos[k]
        cons = [(n, fn) for n, fn in build_programs(fit) if passes_demos(fn, fit)]
        if not cons: continue
        true_key = nxt_out.tobytes() + bytes(nxt_out.shape)
        recs = []; vote = {}
        for n, fn in cons:
            try: p = fn(nxt_in)
            except Exception: p = None
            if not (isinstance(p, np.ndarray) and p.size > 0): continue
            key = p.tobytes() + bytes(p.shape)
            correct = int(key == true_key)
            recs.append(dict(cx=complexity(n), key=key, correct=correct))
            vote[key] = vote.get(key, 0) + 1
            prog_rows.append(dict(task=tid, k=k, cx=complexity(n), correct=correct))
        if not recs: continue
        n_cons = len(recs); distinct = len(vote)
        modal_key = max(vote, key=lambda kk: vote[kk]); modal_frac = vote[modal_key] / n_cons
        random_rate = np.mean([r["correct"] for r in recs])
        shortest = min(recs, key=lambda r: r["cx"])                       # MDL
        shortest_correct = shortest["correct"]
        consensus = max(recs, key=lambda r: (vote[r["key"]], -r["cx"]))   # vote, tie->MDL
        consensus_correct = consensus["correct"]
        any_correct = int(any(r["correct"] for r in recs))
        cell_rows.append(dict(task=tid, k=k, n_consistent=n_cons, distinct=distinct,
                              ambiguous=int(distinct > 1), modal_frac=modal_frac,
                              modal_correct=int(modal_key == true_key),
                              random_rate=random_rate, shortest_correct=shortest_correct,
                              consensus_correct=consensus_correct, any_correct=any_correct))

pp = pd.DataFrame(prog_rows); cc = pd.DataFrame(cell_rows)
pp.to_parquet(f"ablate_prog_{SPLIT}.parquet"); cc.to_parquet(f"ablate_cell_{SPLIT}.parquet")

print(f"=== [{SPLIT}] ===  tasks={cc.task.nunique()}  cells={len(cc)}  programs={len(pp)}")
print("\n(1) Calibration truth — P(generalize | consistent with k demos):")
for k in sorted(pp.k.unique()):
    s = pp[pp.k == k]
    if len(s) >= 20: print(f"   k={k}: {s.correct.mean()*100:5.1f}%  (n_programs={len(s)})")

amb = cc[cc.ambiguous == 1]
print(f"\n(2) The selection problem: {cc.ambiguous.mean()*100:.1f}% of (task,k) cells are AMBIGUOUS "
      f"(>=2 distinct predictions); n_ambiguous={len(amb)}")
if len(amb):
    print("    Accuracy on AMBIGUOUS cells by selection rule:")
    print(f"      random pick    : {amb.random_rate.mean()*100:5.1f}%")
    print(f"      shortest (MDL) : {amb.shortest_correct.mean()*100:5.1f}%")
    print(f"      consensus vote : {amb.consensus_correct.mean()*100:5.1f}%")
    print(f"      oracle ceiling : {amb.any_correct.mean()*100:5.1f}%")

print("\n(3) Is consensus a calibrated confidence? accuracy of modal prediction by modal vote-fraction:")
for lo, hi in [(0.0, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.01)]:
    m = cc[(cc.modal_frac >= lo) & (cc.modal_frac < hi)]
    if len(m) >= 8:
        print(f"   modal_frac[{lo:.1f},{hi:.1f}): acc={m.modal_correct.mean()*100:5.1f}%  (n={len(m)}, mean_conf={m.modal_frac.mean()*100:.0f}%)")
