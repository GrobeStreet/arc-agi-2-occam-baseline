#!/usr/bin/env python3
"""Kaggle Code Competition entrypoint.

The GitHub workflow copies the frozen v3 solver modules into this directory before
publishing the kernel. Kaggle attaches the ARC Prize competition data and executes
this script with internet disabled. The solver writes exactly one required file:

    /kaggle/working/submission.json
"""

from kaggle_submission_v3 import main


if __name__ == "__main__":
    main()
