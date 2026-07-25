# Locking the Kaggle Linked Submission — Step by Step

The ARC Prize 2026 **Paper Track** requires your paper to link to a Kaggle **code submission** on the ARC-AGI-2 track. This notebook (`arc_kaggle_submission.ipynb`) is that submission — the Occam-selection baseline from the paper. It's self-contained, runs on CPU in a couple of minutes, and writes a valid `submission.json`. Its score will be low, and that's fine and on-message: the paper's contribution is the *measurement*, not the solver.

## What you do (≈10 minutes, all clicks)

1. **Open the competition.** Go to the ARC Prize 2026 ARC-AGI-2 competition on Kaggle (the code competition, not the paper page). You must have *joined / accepted the rules* to submit.

2. **Create the notebook.** On the competition page: **Code → New Notebook**. Then **File → Import Notebook → Upload** and select `arc_kaggle_submission.ipynb`. (Or make a blank notebook and paste the one code cell in.)

3. **Attach the data.** In the notebook, click **Add Input** (top-right) and add the competition dataset. The notebook auto-finds the test file (it searches for `*test*challenge*.json` under `/kaggle/input/`). *If it can't find it, open the Input panel, note the exact filename shown, and tell me — I'll adjust one line.*

4. **Run all.** Run → Run All. You should see `wrote submission.json for N tasks` and a sanity line. It writes `/kaggle/working/submission.json`.

5. **Submit.** Click **Save Version** (top-right) → **Save & Run All (Commit)**. When it finishes, open the version → **Submit to Competition** (or use the competition's **Submit Prediction** on the notebook output). This produces a submission on the leaderboard.

6. **Grab the link.** Copy the notebook's public URL (Share → make public) and/or the submission URL. **That URL is what the paper links to** in its "linked Kaggle submission" field.

7. **Submit the paper.** On the Paper Track, upload `ARC_Paper_Draft.pdf` and paste the Kaggle notebook/submission link. Done.

## Honest notes
- I couldn't verify the exact 2026 competition slug and data filename from here (no live Kaggle access), so the notebook is written to **auto-discover** the test file by ARC's standard naming. If your attached dataset names it differently, it's a one-line fix — send me the filename.
- The notebook has **no internet** dependency and installs nothing (uses Kaggle's preinstalled numpy/scipy), so it satisfies the no-network code rule.
- Expected score is ~0% on the hidden set (symbolic search barely engages ARC-AGI-2). The paper says exactly this; a strong Novelty/Theory/Universality paper clears the 4.5 bar without a high Accuracy axis.
- Keep it public so judges can inspect it — reproducibility is our whole brand.

Ping me once it's submitted (or if step 3/5 looks different than described) and I'll handle any adjustment.
