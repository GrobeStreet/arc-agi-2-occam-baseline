#!/usr/bin/env python3
"""Run registered Private Cycle 001 through the official Kaggle CLI.

This orchestrator intentionally contains no representation-development logic. It
builds the frozen v3 notebook, pushes it to Kaggle, waits for execution, submits
the resulting ``submission.json`` to the code competition, and records the score
and currently visible public leaderboard rank.

Authentication is supplied only through environment variables:

- KAGGLE_API_TOKEN
- KAGGLE_USERNAME

The script never prints or writes the token.
"""
from __future__ import annotations

import csv
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CYCLE_DIR = ROOT / "contest" / "private_cycle_001"
KERNEL_DIR = CYCLE_DIR / "kernel"
OUTPUT_DIR = CYCLE_DIR / "kernel_output"
RESULT_PATH = CYCLE_DIR / "result.json"
RESULT_MD_PATH = CYCLE_DIR / "result.md"
COMPETITION = "arc-prize-2026-arc-agi-2"
KERNEL_SLUG = "grobestreet-arc-frozen-v3-cycle-001"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(command: list[str], *, timeout: int = 600) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )


def write_result(state: str, **fields: Any) -> None:
    CYCLE_DIR.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "cycle": "001",
        "competition": COMPETITION,
        "solver": "representation-v3.0-frozen",
        "registration": "HYPOTHESIS-private-v3-cycle-001.md",
        "state": state,
        "updated_at_utc": utc_now(),
        **fields,
    }
    RESULT_PATH.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")

    lines = [
        "# Private Cycle 001 Result",
        "",
        f"**State:** `{state}`  ",
        f"**Competition:** `{COMPETITION}`  ",
        "**Solver:** `representation-v3.0-frozen`  ",
        f"**Updated:** {payload['updated_at_utc']}",
        "",
    ]
    if payload.get("public_score") is not None:
        lines.append(f"- Public/semi-private live score: **{payload['public_score']}**")
    if payload.get("public_rank") not in (None, 0, "0"):
        lines.append(f"- Current public leaderboard rank: **{payload['public_rank']}**")
    if payload.get("kernel_ref"):
        lines.append(f"- Kaggle kernel: `{payload['kernel_ref']}`")
    if payload.get("kernel_version"):
        lines.append(f"- Kernel version: **{payload['kernel_version']}**")
    if payload.get("submission_ref"):
        lines.append(f"- Submission ref: **{payload['submission_ref']}**")
    if payload.get("reason"):
        lines.extend(["", "## Reason", "", str(payload["reason"])])
    lines.extend(
        [
            "",
            "## Representation firewall",
            "",
            "No representation change is authorized by this result. Further expansion requires a newly committed `HYPOTHESIS-representation-cycle-002.md` before source changes or a fresh private-test cycle.",
        ]
    )
    RESULT_MD_PATH.write_text("\n".join(lines) + "\n")


def save_log(name: str, content: str) -> None:
    CYCLE_DIR.mkdir(parents=True, exist_ok=True)
    (CYCLE_DIR / name).write_text(content, encoding="utf-8")


def parse_kernel_version(text: str) -> int | None:
    patterns = [
        r"kernel\s+version\s+(\d+)",
        r"version\s+(\d+)\s+successfully",
        r"versionNumber[\"'=:\s]+(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def parse_submission_detail(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {"raw": text}
    for key, pattern in {
        "submission_ref": r"Submission\s+Ref:\s*(\d+)",
        "status": r"Status:\s*([^\n\r]+)",
        "public_score": r"Public\s+Score:\s*([^\n\r]*)",
        "private_score": r"Private\s+Score:\s*([^\n\r]*)",
    }.items():
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            if key.endswith("score"):
                try:
                    result[key] = float(value) if value else None
                except ValueError:
                    result[key] = value or None
            else:
                result[key] = value
    return result


def find_submission_json() -> Path | None:
    candidates = sorted(OUTPUT_DIR.rglob("submission.json"))
    return candidates[0] if candidates else None


def validate_submission(path: Path) -> dict[str, int]:
    submission = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(submission, dict) or not submission:
        raise ValueError("submission.json is empty or not an object")
    output_count = 0
    for task_id, outputs in submission.items():
        if not isinstance(outputs, list):
            raise ValueError(f"{task_id}: outputs must be a list")
        for index, attempts in enumerate(outputs):
            if set(attempts) != {"attempt_1", "attempt_2"}:
                raise ValueError(f"{task_id}[{index}]: exactly two attempts required")
            output_count += 1
    return {"task_count": len(submission), "output_count": output_count}


def read_public_rank(username: str) -> int | None:
    json_result = run(
        ["kaggle", "competitions", "list", "--group", "entered", "--format", "json"],
        timeout=180,
    )
    save_log("entered_competitions.json.log", json_result.stdout)
    if json_result.returncode == 0:
        try:
            payload = json.loads(json_result.stdout)
            rows = payload if isinstance(payload, list) else payload.get("data", [])
            for row in rows:
                if row.get("ref") == COMPETITION:
                    rank = row.get("userRank")
                    return int(rank) if rank not in (None, "", 0, "0") else None
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    csv_result = run(
        ["kaggle", "competitions", "list", "--group", "entered", "-v"],
        timeout=180,
    )
    save_log("entered_competitions.csv.log", csv_result.stdout)
    if csv_result.returncode == 0:
        try:
            for row in csv.DictReader(csv_result.stdout.splitlines()):
                if row.get("ref") == COMPETITION:
                    rank = row.get("userRank")
                    return int(rank) if rank not in (None, "", "0") else None
        except (TypeError, ValueError):
            pass
    return None


def main() -> int:
    username = os.environ.get("KAGGLE_USERNAME", "").strip()
    token = os.environ.get("KAGGLE_API_TOKEN", "").strip()
    source_commit = os.environ.get("GITHUB_SHA", "unknown")

    if RESULT_PATH.exists():
        try:
            existing = json.loads(RESULT_PATH.read_text())
            if existing.get("state") == "SCORED":
                print("Private Cycle 001 is already scored; refusing a duplicate submission.")
                return 0
        except json.JSONDecodeError:
            pass

    if not username or not token:
        write_result(
            "BLOCKED_AUTH",
            reason=(
                "Kaggle authentication is not configured. Add repository secret "
                "KAGGLE_API_TOKEN and repository variable or secret KAGGLE_USERNAME, "
                "then manually run the Private Cycle 001 workflow."
            ),
            source_commit=source_commit,
        )
        print("Blocked: Kaggle credentials are unavailable.")
        return 0

    version_result = run(["kaggle", "--version"], timeout=120)
    save_log("kaggle_version.log", version_result.stdout)
    if version_result.returncode != 0:
        write_result(
            "ERROR",
            reason="The official Kaggle CLI could not start.",
            source_commit=source_commit,
        )
        return 1

    access_result = run(
        ["kaggle", "competitions", "files", COMPETITION, "--page-size", "1", "-q"],
        timeout=180,
    )
    save_log("competition_access.log", access_result.stdout)
    if access_result.returncode != 0:
        write_result(
            "BLOCKED_RULES_OR_AUTH",
            reason=(
                "Kaggle rejected competition access. Confirm that the account has joined "
                "ARC Prize 2026 and accepted the competition rules, and that the API token "
                "is current."
            ),
            source_commit=source_commit,
            kaggle_username=username,
        )
        return 0

    if KERNEL_DIR.exists():
        shutil.rmtree(KERNEL_DIR)
    build_result = run(
        [
            sys.executable,
            "contest/build_kaggle_kernel_v3.py",
            "--username",
            username,
            "--source-commit",
            source_commit,
        ],
        timeout=180,
    )
    save_log("kernel_build.log", build_result.stdout)
    if build_result.returncode != 0:
        write_result(
            "KERNEL_BUILD_FAILED",
            reason=build_result.stdout[-4000:],
            source_commit=source_commit,
            kaggle_username=username,
        )
        return 1

    manifest = json.loads((CYCLE_DIR / "source_manifest.json").read_text())
    kernel_ref = manifest["kernel_ref"]
    push_result = run(
        ["kaggle", "kernels", "push", "-p", str(KERNEL_DIR), "-t", "900"],
        timeout=1200,
    )
    save_log("kernel_push.log", push_result.stdout)
    if push_result.returncode != 0:
        write_result(
            "KERNEL_PUSH_FAILED",
            reason=push_result.stdout[-4000:],
            source_commit=source_commit,
            kaggle_username=username,
            kernel_ref=kernel_ref,
            source_manifest=manifest,
        )
        return 0

    kernel_version = parse_kernel_version(push_result.stdout) or 1
    final_kernel_status = "UNKNOWN"
    status_log: list[str] = []
    deadline = time.time() + 5400
    while time.time() < deadline:
        status_result = run(["kaggle", "kernels", "status", kernel_ref], timeout=180)
        snapshot = status_result.stdout.strip()
        status_log.append(f"[{utc_now()}]\n{snapshot}\n")
        lower = snapshot.lower()
        if status_result.returncode == 0 and (
            "complete" in lower or "success" in lower
        ):
            final_kernel_status = "COMPLETE"
            break
        if any(word in lower for word in ("error", "failed", "cancelled", "canceled")):
            final_kernel_status = "FAILED"
            break
        time.sleep(20)
    save_log("kernel_status.log", "\n".join(status_log))

    if final_kernel_status != "COMPLETE":
        write_result(
            "KERNEL_EXECUTION_FAILED" if final_kernel_status == "FAILED" else "KERNEL_TIMEOUT",
            reason=status_log[-1][-4000:] if status_log else "No kernel status returned.",
            source_commit=source_commit,
            kaggle_username=username,
            kernel_ref=kernel_ref,
            kernel_version=kernel_version,
            source_manifest=manifest,
        )
        return 0

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_result = run(
        ["kaggle", "kernels", "output", kernel_ref, "-p", str(OUTPUT_DIR), "-o"],
        timeout=900,
    )
    save_log("kernel_output.log", output_result.stdout)
    submission_path = find_submission_json()
    if output_result.returncode != 0 or submission_path is None:
        write_result(
            "KERNEL_OUTPUT_MISSING",
            reason=output_result.stdout[-4000:],
            source_commit=source_commit,
            kaggle_username=username,
            kernel_ref=kernel_ref,
            kernel_version=kernel_version,
            source_manifest=manifest,
        )
        return 0

    validation = validate_submission(submission_path)
    submit_help = run(["kaggle", "competitions", "submit", "--help"], timeout=120)
    command = [
        "kaggle",
        "competitions",
        "submit",
        COMPETITION,
        "-f",
        "submission.json",
        "-k",
        kernel_ref,
        "-v",
        str(kernel_version),
        "-m",
        f"Frozen representation v3 Private Cycle 001; source {source_commit[:12]}",
    ]
    if "--wait" in submit_help.stdout:
        command.extend(["--wait", "7200", "--poll-interval", "20"])
    submit_result = run(command, timeout=7500)
    save_log("competition_submit.log", submit_result.stdout)

    ref_match = re.search(r"Submission\s+ref:\s*(\d+)", submit_result.stdout, re.I)
    submission_ref = ref_match.group(1) if ref_match else None
    detail: dict[str, Any] = parse_submission_detail(submit_result.stdout)
    if submission_ref and "submission_ref" not in detail:
        detail["submission_ref"] = submission_ref

    if submission_ref:
        detail_result = run(
            ["kaggle", "competitions", "submission", submission_ref], timeout=180
        )
        save_log("competition_submission_detail.log", detail_result.stdout)
        if detail_result.returncode == 0:
            detail.update(
                {
                    key: value
                    for key, value in parse_submission_detail(detail_result.stdout).items()
                    if key != "raw" and value is not None
                }
            )

    submissions_result = run(
        ["kaggle", "competitions", "submissions", COMPETITION, "-v", "-q"],
        timeout=180,
    )
    save_log("competition_submissions.csv", submissions_result.stdout)
    public_rank = read_public_rank(username)

    state = "SCORED" if detail.get("public_score") is not None else "SUBMITTED_PENDING"
    if submit_result.returncode != 0 and submission_ref is None:
        state = "SUBMISSION_FAILED"

    write_result(
        state,
        source_commit=source_commit,
        kaggle_username=username,
        kernel_ref=kernel_ref,
        kernel_version=kernel_version,
        kernel_status=final_kernel_status,
        submission_ref=detail.get("submission_ref"),
        submission_status=detail.get("status"),
        public_score=detail.get("public_score"),
        private_score=detail.get("private_score"),
        public_rank=public_rank,
        validation=validation,
        source_manifest=manifest,
        reason=(submit_result.stdout[-4000:] if state == "SUBMISSION_FAILED" else None),
        ranking_note=(
            "This is the current Kaggle live/semi-private public rank. The final private "
            "leaderboard rank is unavailable until the competition concludes."
        ),
    )
    print(RESULT_PATH.read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
