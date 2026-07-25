"""Run the DSL solver over an ARC-AGI-2 split; record, per task, all demo-passing
programs and whether each generalizes to the test output. Outputs a parquet for
the calibration analysis."""
import json, glob, os, sys, numpy as np, pandas as pd
from dsl import build_programs, passes_demos, complexity

SPLIT = sys.argv[1] if len(sys.argv) > 1 else "evaluation"
ROOT = "/home/claude/ARC-AGI-2/data/" + SPLIT
files = sorted(glob.glob(ROOT + "/*.json"))

rows = []
for f in files:
    tid = os.path.basename(f)[:-5]
    t = json.load(open(f))
    train_pairs = [(np.array(p["input"]), np.array(p["output"])) for p in t["train"]]
    tests = [(np.array(p["input"]), np.array(p["output"])) for p in t["test"]]
    progs = build_programs(train_pairs)
    passers = [(n, fn) for n, fn in progs if passes_demos(fn, train_pairs)]
    # dedupe passers by their behavior on the FIRST test input (distinct predictions)
    for ti, (xin, ytrue) in enumerate(tests):
        preds = []  # (name, complexity, correct, pred_key)
        seen = {}
        for n, fn in passers:
            try:
                p = fn(xin)
            except Exception:
                continue
            if p is None or not isinstance(p, np.ndarray): continue
            key = p.tobytes() + bytes(p.shape)
            correct = (p.shape == ytrue.shape and np.array_equal(p, ytrue))
            preds.append(dict(name=n, cx=complexity(n), correct=int(correct), key=key))
        n_pass = len(preds)
        distinct = len(set(p["key"] for p in preds))
        # consensus over distinct predictions (vote by count of passing programs)
        vote = {}
        for p in preds: vote[p["key"]] = vote.get(p["key"], 0) + 1
        modal_key = max(vote, key=vote.get) if vote else None
        modal_frac = (vote[modal_key] / n_pass) if n_pass else 0.0
        # selection rules -> did the picked program get it right?
        def picked_correct(rule):
            if not preds: return np.nan
            if rule == "first": pick = preds[0]
            elif rule == "shortest": pick = min(preds, key=lambda p: p["cx"])
            elif rule == "consensus": pick = max(preds, key=lambda p: (vote[p["key"]], -p["cx"]))
            return pick["correct"]
        any_correct = int(any(p["correct"] for p in preds))
        rows.append(dict(task=tid, ti=ti, n_pass=n_pass, distinct=distinct,
                         modal_frac=modal_frac, any_correct=any_correct,
                         first=picked_correct("first"), shortest=picked_correct("shortest"),
                         consensus=picked_correct("consensus")))

df = pd.DataFrame(rows)
df.to_parquet(f"solver_{SPLIT}.parquet")
n_tasks = df.task.nunique()
solved_any = df[df.n_pass > 0]
print(f"[{SPLIT}] {len(df)} test-inputs over {n_tasks} tasks")
print(f"  tasks-with-≥1-demo-passing-program: {(df.n_pass>0).mean()*100:.1f}%")
if len(solved_any):
    print(f"  among those, MULTIPLE distinct test-predictions (selection needed): {(solved_any.distinct>1).mean()*100:.1f}%")
    print(f"  demo-pass→generalize (any passing prog correct): {solved_any.any_correct.mean()*100:.1f}%")
    for r in ["first", "shortest", "consensus"]:
        print(f"  pass@1 accuracy via '{r}' selection (of solvable): {solved_any[r].mean()*100:.1f}%")
    # overall pass@1 on the whole split (unsolved count as wrong)
    for r in ["first", "shortest", "consensus"]:
        print(f"  OVERALL pass@1 '{r}': {df[r].fillna(0).mean()*100:.2f}%")
