#!/usr/bin/env python3
"""Run the registered frozen-v3 Kaggle private cycle from CI.

This orchestration script never changes the frozen solver. It copies the exact
v3 files from a pinned Git commit into a Kaggle kernel bundle, runs the official
Kaggle CLI, submits the resulting code-kernel version, and writes a publish-
regardless result record. Missing credentials, unaccepted rules, runtime errors,
and a zero score are all preserved as outcomes rather than hidden.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
COMPETITION = "arc-prize-2026-arc-agi-2"
KERNEL_SLUG = "arc-frozen-v3-cycle-001"
FROZEN_COMMIT = "70672f3aa62d089bfffd072461a5713caae1e099"
FROZEN_FILES = [
    "dsl.py",
    "dsl_v3.py",
    "benchmark_representation_v3.py",
    "kaggle_submission_v3.py",
]
RESULT_DIR = REPO / "results" / "private_cycle_001"
KERNEL_DIR = REPO / "contest" / "kaggle_kernel_v3" / "build"
LOG_DIR = RESULT_DIR / "logs"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def tail(text: str, limit: int = 12000) -> str:
    return text[-limit:]


def run(command: list[str], *, timeout: int = 900) -> dict[str, Any]:
    started = time.time()
    try:
        completed = subprocess.run(
            command,
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
        return {
            "command": command,
            "returncode": completed.returncode,
            "seconds": round(time.time() - started, 3),
            "output": completed.stdout or "",
        }
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or "") + (exc.stderr or "")
        return {
            "command": command,
            "returncode": 124,
            "seconds": round(time.time() - started, 3),
            "output": str(output),
            "timeout": timeout,
        }


def git_show(commit: str, path: str) -> bytes:
    completed = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Unable to read {path} from {commit}: "
            + completed.stderr.decode("utf-8", errors="replace")
        )
    return completed.stdout


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_records(result: dict[str, Any]) -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    (RESULT_DIR / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    score = result.get("public_score")
    rank = result.get("public_rank")
    score_text = "not available" if score in (None, "") else str(score)
    rank_text = "not available" if rank in (None, "", 0, "0") else str(rank)
    lines = [
        "# Frozen v3 Private Cycle 001 — Result",
        "",
        f"**State:** {result.get('state', 'UNKNOWN')}  ",
        f"**Competition:** `{COMPETITION}`  ",
        f"**Frozen source commit:** `{FROZEN_COMMIT}`  ",
        f"**Recorded:** {result.get('updated_at', utc_now())}",
        "",
        f"- Kaggle kernel: `{result.get('kernel_ref') or 'not created'}`",
        f"- Kernel version: `{result.get('kernel_version') or 'not available'}`",
        f"- Submission ref: `{result.get('submission_ref') or 'not available'}`",
        f"- Submission status: `{result.get('submission_status') or 'not available'}`",
        f"- Visible public score: **{score_text}**",
        f"- Visible public rank: **{rank_text}**",
        "",
        "## Interpretation",
        "",
        result.get(
            "interpretation",
            "The frozen result has not yet reached a scored Kaggle submission.",
        ),
        "",
        "## Expansion firewall",
        "",
        "No representation change is authorized under Cycle 001. Any subsequent "
        "representation work requires a new precommitted "
        "`HYPOTHESIS-representation-cycle-002.md`.",
    ]
    if result.get("error"):
        lines.extend(["", "## Recorded blocker or error", "", f"```text\n{result['error']}\n```"])
    (RESULT_DIR / "RESULT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_kernel_version(text: str) -> int | None:
    patterns = [
        r"[Kk]ernel\s+version\s+(\d+)",
        r"/versions/(\d+)",
        r"[Vv]ersion\s*[:#]?\s*(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    return None


def parse_submission_status(text: str) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    patterns = {
        "submission_ref": r"Submission\s+Ref:\s*(\d+)",
        "submission_status": r"Status:\s*([^\r\n]+)",
        "public_score": r"Public\s+Score:\s*([^\r\n]*)",
        "private_score": r"Private\s+Score:\s*([^\r\n]*)",
        "submission_date": r"Submission\s+Date:\s*([^\r\n]+)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            fields[key] = value or None
    return fields


def parse_rank_from_entered_csv(text: str) -> int | None:
    try:
        rows = list(csv.DictReader(text.splitlines()))
    except Exception:
        return None
    for row in rows:
        ref = row.get("ref") or row.get("competition") or row.get("Ref")
        if ref == COMPETITION:
            raw = row.get("userRank") or row.get("user_rank") or row.get("rank")
            try:
                return int(float(raw)) if raw not in (None, "") else None
            except (TypeError, ValueError):
                return None
    return None


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(KERNEL_DIR, ignore_errors=True)
    KERNEL_DIR.mkdir(parents=True, exist_ok=True)

    username = os.environ.get("KAGGLE_USERNAME", "").strip()
    token = os.environ.get("KAGGLE_API_TOKEN", "").strip()
    kernel_ref = f"{username}/{KERNEL_SLUG}" if username else None
    result: dict[str, Any] = {
        "cycle": "private-v3-cycle-001",
        "competition": COMPETITION,
        "state": "INITIALIZING",
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "workflow_source_commit": os.environ.get("GITHUB_SHA"),
        "frozen_source_commit": FROZEN_COMMIT,
        "kernel_ref": kernel_ref,
        "kernel_version": None,
        "submission_ref": None,
        "submission_status": None,
        "public_score": None,
        "private_score": None,
        "public_rank": None,
        "source_hashes": {},
        "commands": [],
    }

    try:
        # Materialize only the registered frozen source version.
        for relative in FROZEN_FILES:
            destination = KERNEL_DIR / Path(relative).name
            destination.write_bytes(git_show(FROZEN_COMMIT, relative))
            result["source_hashes"][relative] = sha256(destination)

        entrypoint = REPO / "contest" / "kaggle_kernel_v3" / "run.py"
        shutil.copy2(entrypoint, KERNEL_DIR / "run.py")
        result["source_hashes"]["contest/kaggle_kernel_v3/run.py"] = sha256(
            KERNEL_DIR / "run.py"
        )
        (RESULT_DIR / "SOURCE_SHA256SUMS.json").write_text(
            json.dumps(result["source_hashes"], indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except Exception as exc:
        result.update(
            state="SOURCE_FREEZE_ERROR",
            error=str(exc),
            interpretation="The registered frozen source could not be materialized; no submission was attempted.",
            updated_at=utc_now(),
        )
        write_records(result)
        return 0

    if not username or not token:
        missing = [
            name
            for name, value in (
                ("KAGGLE_USERNAME", username),
                ("KAGGLE_API_TOKEN", token),
            )
            if not value
        ]
        result.update(
            state="BLOCKED_AUTH",
            error="Missing GitHub Actions secret(s): " + ", ".join(missing),
            interpretation=(
                "The frozen kernel is prepared and hashed, but Kaggle authentication is not configured. "
                "No contest submission or ranking exists yet."
            ),
            updated_at=utc_now(),
        )
        write_records(result)
        return 0

    metadata = {
        "id": kernel_ref,
        "title": "ARC Frozen Representation v3 — Private Cycle 001",
        "code_file": "run.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": False,
        "enable_internet": False,
        "competition_sources": [COMPETITION],
        "dataset_sources": [],
        "kernel_sources": [],
    }
    (KERNEL_DIR / "kernel-metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )

    # Confirm API access and rule acceptance before creating a kernel version.
    preflight = run(
        ["kaggle", "competitions", "files", COMPETITION, "--page-size", "1", "-q"],
        timeout=180,
    )
    result["commands"].append({**preflight, "output": tail(preflight["output"])})
    (LOG_DIR / "01_preflight.txt").write_text(preflight["output"], encoding="utf-8")
    if preflight["returncode"] != 0:
        result.update(
            state="BLOCKED_RULES_OR_AUTH",
            error=tail(preflight["output"]),
            interpretation=(
                "Kaggle rejected competition access. The account must accept the ARC Prize 2026 rules "
                "and provide a current API token before Cycle 001 can run."
            ),
            updated_at=utc_now(),
        )
        write_records(result)
        return 0

    push = run(
        ["kaggle", "kernels", "push", "-p", str(KERNEL_DIR), "-t", "43200"],
        timeout=43260,
    )
    result["commands"].append({**push, "output": tail(push["output"])})
    (LOG_DIR / "02_kernel_push.txt").write_text(push["output"], encoding="utf-8")
    if push["returncode"] != 0:
        result.update(
            state="KERNEL_PUSH_FAILED",
            error=tail(push["output"]),
            interpretation="The frozen kernel upload or Kaggle execution failed before competition submission.",
            updated_at=utc_now(),
        )
        write_records(result)
        return 0

    version = parse_kernel_version(push["output"])
    result["kernel_version"] = version
    if version is None:
        result.update(
            state="KERNEL_VERSION_UNRESOLVED",
            error=(
                "The official CLI reported a successful kernel push but its output did not expose a "
                "version number that could be submitted safely. See 02_kernel_push.txt."
            ),
            interpretation="No competition submission was made because the exact immutable kernel version was not resolved.",
            updated_at=utc_now(),
        )
        write_records(result)
        return 0

    # Verify the expected output exists in the completed kernel version.
    output_dir = RESULT_DIR / "kernel_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    kernel_output = run(
        ["kaggle", "kernels", "output", kernel_ref, "-p", str(output_dir), "-o", "-q"],
        timeout=600,
    )
    result["commands"].append(
        {**kernel_output, "output": tail(kernel_output["output"])}
    )
    (LOG_DIR / "03_kernel_output.txt").write_text(
        kernel_output["output"], encoding="utf-8"
    )
    if kernel_output["returncode"] != 0 or not (output_dir / "submission.json").exists():
        result.update(
            state="KERNEL_OUTPUT_FAILED",
            error=tail(kernel_output["output"]) or "submission.json was not produced",
            interpretation="The kernel version completed without a usable submission.json; no contest submission was made.",
            updated_at=utc_now(),
        )
        write_records(result)
        return 0

    submission_message = "Frozen representation v3 — registered private Cycle 001"
    submit = run(
        [
            "kaggle",
            "competitions",
            "submit",
            COMPETITION,
            "-f",
            "submission.json",
            "-k",
            kernel_ref,
            "-v",
            str(version),
            "-m",
            submission_message,
            "--wait",
            "43200",
            "--poll-interval",
            "30",
        ],
        timeout=43260,
    )
    result["commands"].append({**submit, "output": tail(submit["output"])})
    (LOG_DIR / "04_submission.txt").write_text(submit["output"], encoding="utf-8")
    submit_fields = parse_submission_status(submit["output"])
    result.update({key: value for key, value in submit_fields.items() if value is not None})

    # Newer CLI prints only the submission ref from submit; ask for the final status explicitly.
    ref_match = re.search(r"Submission\s+ref:\s*(\d+)", submit["output"], re.IGNORECASE)
    if ref_match:
        result["submission_ref"] = ref_match.group(1)
    if result.get("submission_ref"):
        status = run(
            ["kaggle", "competitions", "submission", str(result["submission_ref"])],
            timeout=180,
        )
        result["commands"].append({**status, "output": tail(status["output"])})
        (LOG_DIR / "05_submission_status.txt").write_text(
            status["output"], encoding="utf-8"
        )
        result.update(
            {
                key: value
                for key, value in parse_submission_status(status["output"]).items()
                if value is not None
            }
        )

    # The official competition list exposes the authenticated user's public rank.
    entered = run(
        ["kaggle", "competitions", "list", "--group", "entered", "-v"],
        timeout=180,
    )
    result["commands"].append({**entered, "output": tail(entered["output"])})
    (LOG_DIR / "06_entered_competitions.csv").write_text(
        entered["output"], encoding="utf-8"
    )
    result["public_rank"] = parse_rank_from_entered_csv(entered["output"])

    leaderboard_dir = RESULT_DIR / "leaderboard"
    leaderboard_dir.mkdir(parents=True, exist_ok=True)
    leaderboard = run(
        [
            "kaggle",
            "competitions",
            "leaderboard",
            COMPETITION,
            "-d",
            "-p",
            str(leaderboard_dir),
            "-q",
        ],
        timeout=300,
    )
    result["commands"].append(
        {**leaderboard, "output": tail(leaderboard["output"])}
    )
    (LOG_DIR / "07_leaderboard_download.txt").write_text(
        leaderboard["output"], encoding="utf-8"
    )

    score = result.get("public_score")
    if submit["returncode"] != 0:
        state = "SUBMISSION_FAILED_OR_TIMED_OUT"
        interpretation = (
            "Kaggle did not return a completed scored submission. The frozen kernel and logs are preserved; "
            "the solver was not changed."
        )
        error = tail(submit["output"])
    elif score in (None, ""):
        state = "SUBMITTED_SCORE_PENDING"
        interpretation = "Kaggle accepted the frozen code submission, but a public score was not yet available."
        error = None
    else:
        try:
            numeric_score = float(score)
        except (TypeError, ValueError):
            numeric_score = None
        if numeric_score is not None and numeric_score > 0:
            state = "SCORED_NONZERO"
            interpretation = (
                "The frozen v3 artifact achieved a nonzero visible Kaggle score. This is the immutable "
                "Cycle 001 result; no task-level tuning is permitted from it."
            )
        elif numeric_score == 0:
            state = "SCORED_NULL"
            interpretation = (
                "The frozen v3 artifact scored zero on the visible Kaggle leaderboard. The null result is "
                "preserved, and representation changes require a newly registered Cycle 002."
            )
        else:
            state = "SCORED_UNPARSEABLE"
            interpretation = "Kaggle returned a score that could not be interpreted numerically."
        error = None

    result.update(
        state=state,
        interpretation=interpretation,
        error=error,
        updated_at=utc_now(),
    )
    write_records(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
