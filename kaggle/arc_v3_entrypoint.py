#!/usr/bin/env python3
"""Canonical Kaggle notebook/script entrypoint for Private Cycle 001.

This imports the frozen representation-v3 submission code and writes the required
`/kaggle/working/submission.json`. No grammar, ranking, fallback, or output-policy
change is made here.
"""

from kaggle_submission_v3 import main


if __name__ == "__main__":
    main()
