"""ARC-AGI-2 baseline submission: description-length (Occam) program selection.
For each test input we enumerate demonstration-consistent programs and select by
(consensus vote, then minimum description length). pass@2 = the two most-supported
distinct predictions. This is the reproducible baseline linked from the paper; its
purpose is to demonstrate the selection rule, not to top the leaderboard.

Usage:
  python kaggle_solver.py CHALLENGES.json           -> writes submission.json
  python kaggle_solver.py evaluation --score        -> local pass@2 score on public eval
"""
import json, glob, os, sys, numpy as np
from dsl import build_programs, passes_demos, complexity

def solve_one(train_pairs, test_input):
    """Return (attempt_1_grid, attempt_2_grid) as python lists."""
    x = np.array(test_input)
    progs = build_programs(train_pairs)
    cons = [(n, fn) for n, fn in progs if passes_demos(fn, train_pairs)]
    preds = {}  # pred_key -> dict(grid, votes, min_cx)
    for n, fn in cons:
        try: p = fn(x)
        except Exception: p = None
        if not (isinstance(p, np.ndarray) and p.size > 0): continue
        key = p.tobytes() + bytes(p.shape)
        d = preds.get(key)
        if d is None: preds[key] = dict(grid=p, votes=1, min_cx=complexity(n))
        else:
            d["votes"] += 1; d["min_cx"] = min(d["min_cx"], complexity(n))
    ranked = sorted(preds.values(), key=lambda d: (-d["votes"], d["min_cx"]))
    # fallbacks when the solver finds <2 candidates
    fb = [x, np.rot90(x, 2)]
    grids = [d["grid"] for d in ranked] + fb
    a1 = grids[0]; a2 = next((g for g in grids[1:] if g.shape != a1.shape or not np.array_equal(g, a1)), fb[0])
    return a1.tolist(), a2.tolist()

def build_submission(challenges):
    sub = {}
    for tid, t in challenges.items():
        tp = [(np.array(p["input"]), np.array(p["output"])) for p in t["train"]]
        outs = []
        for tc in t["test"]:
            a1, a2 = solve_one(tp, tc["input"])
            outs.append({"attempt_1": a1, "attempt_2": a2})
        sub[tid] = outs
    return sub

if __name__ == "__main__":
    arg = sys.argv[1]
    score = "--score" in sys.argv
    if arg in ("training", "evaluation"):  # local dirs with ground-truth
        files = sorted(glob.glob(f"/home/claude/ARC-AGI-2/data/{arg}/*.json"))
        challenges = {os.path.basename(f)[:-5]: json.load(open(f)) for f in files}
    else:
        challenges = json.load(open(arg))
    sub = build_submission(challenges)
    json.dump(sub, open("submission.json", "w"))
    print(f"wrote submission.json for {len(sub)} tasks")
    if score and arg in ("training", "evaluation"):
        correct = total = 0
        for tid, t in challenges.items():
            for i, tc in enumerate(t["test"]):
                if "output" not in tc: continue
                y = np.array(tc["output"]); total += 1
                atts = sub[tid][i]
                ok = any(np.array_equal(np.array(atts[a]), y) for a in ("attempt_1", "attempt_2")
                         if np.array(atts[a]).shape == y.shape)
                correct += int(ok)
        print(f"pass@2 on {arg}: {correct}/{total} = {100*correct/total:.2f}%")
