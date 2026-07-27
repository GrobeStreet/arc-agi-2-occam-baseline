#!/usr/bin/env python3
"""Build the self-contained Kaggle notebook for Private Cycle 001.

The notebook embeds the exact committed frozen-v3 sources as base64, reconstructs
them inside /kaggle/working, and runs the normal submission entrypoint with
internet disabled. This avoids relying on GitHub access from Kaggle and gives the
workflow a deterministic source-hash manifest.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Any


SOURCE_FILES = (
    "dsl.py",
    "dsl_v3.py",
    "kaggle_submission_v3.py",
)
COMPETITION = "arc-prize-2026-arc-agi-2"
KERNEL_SLUG = "grobestreet-arc-frozen-v3-cycle-001"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def make_notebook(encoded: dict[str, str], source_commit: str) -> dict[str, Any]:
    cell_source = f'''# Frozen ARC Representation v3 — Private Cycle 001\n# Source commit: {source_commit}\nimport base64\nimport json\nimport os\nimport pathlib\nimport sys\n\nENCODED_SOURCES = {json.dumps(encoded, sort_keys=True)}\nWORKING = pathlib.Path("/kaggle/working")\nWORKING.mkdir(parents=True, exist_ok=True)\nfor filename, payload in ENCODED_SOURCES.items():\n    (WORKING / filename).write_bytes(base64.b64decode(payload.encode("ascii")))\n\nos.chdir(WORKING)\nsys.path.insert(0, str(WORKING))\nsys.argv = [\n    "kaggle_submission_v3.py",\n    "--output", str(WORKING / "submission.json"),\n    "--metadata", str(WORKING / "submission_v3_metadata.json"),\n]\nimport kaggle_submission_v3\nkaggle_submission_v3.main()\n\nsubmission = json.loads((WORKING / "submission.json").read_text())\nassert submission, "submission.json is empty"\nfor task_id, outputs in submission.items():\n    assert isinstance(outputs, list), task_id\n    for index, attempts in enumerate(outputs):\n        assert set(attempts) == {{"attempt_1", "attempt_2"}}, (task_id, index)\nprint(f"Validated frozen v3 submission for {{len(submission)}} private tasks")\n'''
    return {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# GrobeStreet ARC Frozen V3 — Private Cycle 001\n",
                    "This notebook is generated from the registered, frozen v3 sources. ",
                    "It writes exactly two attempts per private test input.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": cell_source.splitlines(keepends=True),
            },
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11"},
            "private_cycle": {
                "cycle": "001",
                "solver": "representation-v3.0-frozen",
                "source_commit": source_commit,
                "registration": "HYPOTHESIS-private-v3-cycle-001.md",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--output-dir", default="contest/private_cycle_001/kernel")
    parser.add_argument("--source-commit", default=os.environ.get("GITHUB_SHA", "unknown"))
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    output_dir = root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    encoded: dict[str, str] = {}
    manifest: dict[str, Any] = {
        "cycle": "001",
        "solver": "representation-v3.0-frozen",
        "competition": COMPETITION,
        "source_commit": args.source_commit,
        "source_files": {},
    }
    for filename in SOURCE_FILES:
        path = root / filename
        if not path.exists():
            raise FileNotFoundError(path)
        encoded[filename] = base64.b64encode(path.read_bytes()).decode("ascii")
        manifest["source_files"][filename] = {
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
        }

    notebook_name = "frozen_v3_cycle_001.ipynb"
    notebook = make_notebook(encoded, args.source_commit)
    (output_dir / notebook_name).write_text(
        json.dumps(notebook, indent=1) + "\n", encoding="utf-8"
    )

    username = args.username.strip()
    if not username or "/" in username:
        raise ValueError("Kaggle username is missing or invalid")
    kernel_ref = f"{username}/{KERNEL_SLUG}"
    metadata = {
        "id": kernel_ref,
        "title": "GrobeStreet ARC Frozen V3 Cycle 001",
        "code_file": notebook_name,
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": False,
        "enable_internet": False,
        "dataset_sources": [],
        "competition_sources": [COMPETITION],
        "kernel_sources": [],
        "model_sources": [],
    }
    (output_dir / "kernel-metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    manifest["kernel_ref"] = kernel_ref
    manifest["notebook_sha256"] = sha256(output_dir / notebook_name)
    (output_dir.parent / "source_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
