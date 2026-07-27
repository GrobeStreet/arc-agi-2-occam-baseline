#!/usr/bin/env python3
"""Execute the registered frozen-v3 Kaggle Private Cycle 001.

This runner changes packaging and evidence capture only. It materializes the four
frozen solver files from commit 70672f3, embeds them in one self-contained Kaggle
notebook, runs that exact kernel with internet disabled, submits the immutable
kernel version to the ARC Prize 2026 code competition, and records the visible
score and public rank. Every blocked, failed, null, or positive outcome is saved.
"""

from __future__ import annotations

import csv
import hashlib
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


REPO = Path(__file__).resolve().parents[1]
COMPETITION = "arc-prize-2026-arc-agi-2"
KERNEL_SLUG = "grobestreet-arc-frozen-v3-cycle-001"
FROZEN_COMMIT = "70672f3aa62d089bfffd072461a5713caae1e099"
FROZEN_FILES = (
    "dsl.py",
    "dsl_v3.py",
    "benchmark_representation_v3.py",
    "kaggle_submission_v3.py",
)
RESULT_DIR = REPO / "results" / "private_cycle_001"
LOG_DIR = RESULT_DIR / "logs"
KERNEL_DIR = REPO / "contest" / "kaggle_kernel_v3" / "build"
SOURCE_DIR = KERNEL_DIR / "frozen_source"
NOTEBOOK = KERNEL_DIR / "frozen_v3_cycle_001.ipynb"
MANIFEST = KERNEL_DIR / "source_manifest.json"
TERMINAL_STATES = {"SCORED_NONZERO", "SCORED_NULL"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def tail(text: str, limit: int = 16000) -> str:
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
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {
            "command": command,
            "returncode": 124,
            "seconds": round(time.time() - started, 3),
            "output": stdout + stderr,
            "timeout": timeout,
        }


def log_command(name: str, result: dict[str, Any], record: dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / name).write_text(result.get("output", ""), encoding="utf-8")
    safe = dict(result)
    safe["output"] = tail(str(safe.get("output", "")))
    record.setdefault("commands", []).append(safe)


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


def load_existing() -> dict[str, Any] | None:
    path = RESULT_DIR / "result.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_records(record: dict[str, Any]) -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    record["updated_at"] = utc_now()
    (RESULT_DIR / "result.json").write_text(
        json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    public_score = record.get("public_score")
    public_rank = record.get("public_rank")
    lines = [
        "# Frozen V3 Private Cycle 001 — Kaggle Result",
        "",
        f"**State:** `{record.get('state', 'UNKNOWN')}`  ",
        f"**Competition:** `{COMPETITION}`  ",
        f"**Frozen source:** `{FROZEN_COMMIT}`  ",
        f"**Recorded:** {record['updated_at']}",
        "",
        "## Official competition record",
        "",
        f"- Kernel: `{record.get('kernel_ref') or 'not created'}`",
        f"- Kernel version: `{record.get('kernel_version') or 'not available'}`",
        f"- Submission ref: `{record.get('submission_ref') or 'not available'}`",
        f"- Submission status: `{record.get('submission_status') or 'not available'}`",
        f"- Visible public score: **{public_score if public_score is not None else 'not available'}**",
        f"- Visible public rank: **{public_rank if public_rank not in (None, 0) else 'not available'}**",
        f"- Teams in snapshot: **{record.get('team_count') or 'not available'}**",
        f"- Final private score: **{record.get('private_score') if record.get('private_score') is not None else 'not available'}**",
        "",
        "## Interpretation",
        "",
        record.get("interpretation", "No interpretation recorded."),
        "",
        "## Representation firewall",
        "",
        "Cycle 001 authorizes no representation edits. Any expansion requires a new "
        "`HYPOTHESIS-representation-cycle-002.md` committed before the source change.",
    ]
    if record.get("error"):
        lines.extend(["", "## Blocker or error", "", "```text", str(record["error"]), "```"])
    (RESULT_DIR / "RESULT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def initial_record(username: str) -> dict[str, Any]:
    return {
        "cycle": "private-v3-cycle-001",
        "competition": COMPETITION,
        "state": "INITIALIZING",
        "created_at": utc_now(),
        "workflow_source_commit": os.environ.get("GITHUB_SHA"),
        "frozen_source_commit": FROZEN_COMMIT,
        "registration": "HYPOTHESIS-private-v3-cycle-001.md",
        "packaging_note": "PRIVATE_CYCLE_001_PACKAGING_NOTE.md",
        "kernel_ref": f"{username}/{KERNEL_SLUG}" if username else None,
        "kernel_version": None,
        "submission_ref": None,
        "submission_status": None,
        "public_score": None,
        "private_score": None,
        "public_rank": None,
        "team_count": None,
        "source_hashes": {},
        "commands": [],
    }


def materialize_frozen_source(record: dict[str, Any]) -> None:
    shutil.rmtree(KERNEL_DIR, ignore_errors=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    for relative in FROZEN_FILES:
        destination = SOURCE_DIR / Path(relative).name
        destination.write_bytes(git_show(FROZEN_COMMIT, relative))
        record["source_hashes"][relative] = sha256(destination)

    builder = run(
        [
            sys.executable,
            "scripts/build_frozen_v3_kaggle_notebook.py",
            "--root",
            str(SOURCE_DIR),
            "--output",
            str(NOTEBOOK),
            "--manifest",
            str(MANIFEST),
            "--source-commit",
            FROZEN_COMMIT,
        ],
        timeout=180,
    )
    log_command("00_build_notebook.txt", builder, record)
    if builder["returncode"] != 0 or not NOTEBOOK.is_file():
        raise RuntimeError("Unable to build the self-contained frozen notebook: " + tail(builder["output"]))

    record["source_hashes"][str(NOTEBOOK.relative_to(REPO))] = sha256(NOTEBOOK)
    record["source_manifest"] = json.loads(MANIFEST.read_text(encoding="utf-8"))
    (RESULT_DIR / "SOURCE_SHA256SUMS.json").write_text(
        json.dumps(record["source_hashes"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    shutil.copy2(MANIFEST, RESULT_DIR / "source_manifest.json")


def write_kernel_metadata(username: str) -> None:
    metadata = {
        "id": f"{username}/{KERNEL_SLUG}",
        "title": "GrobeStreet ARC Frozen V3 Private Cycle 001",
        "code_file": NOTEBOOK.name,
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": False,
        "enable_internet": False,
        "competition_sources": [COMPETITION],
        "dataset_sources": [],
        "kernel_sources": [],
        "model_sources": [],
    }
    (KERNEL_DIR / "kernel-metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )


def parse_kernel_version(text: str) -> int | None:
    for pattern in (
        r"(?i)kernel\s+version\s+(\d+)",
        r"(?i)version\s+(\d+)\s+successfully",
        r"/versions/(\d+)",
        r"(?i)version\s*[:#]?\s*(\d+)",
    ):
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    return None


def parse_status_output(text: str) -> str:
    return " ".join(text.strip().split())


def wait_for_kernel(kernel_ref: str, record: dict[str, Any]) -> bool:
    lines: list[str] = []
    for attempt in range(1, 181):
        status = run(["kaggle", "kernels", "status", kernel_ref], timeout=120)
        normalized = parse_status_output(status["output"])
        lines.append(f"[{attempt:03d}] rc={status['returncode']} {normalized}")
        lowered = normalized.lower()
        if status["returncode"] == 0 and any(token in lowered for token in ("complete", "success")):
            (LOG_DIR / "03_kernel_status.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
            return True
        if any(token in lowered for token in ("error", "failed", "cancel")):
            (LOG_DIR / "03_kernel_status.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
            record["error"] = normalized
            return False
        time.sleep(20)
    (LOG_DIR / "03_kernel_status.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    record["error"] = "Timed out while waiting for Kaggle kernel completion."
    return False


def validate_submission(path: Path) -> tuple[int, int]:
    submission = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(submission, dict) or not submission:
        raise ValueError("submission.json is empty or not a task mapping")
    output_count = 0
    for task_id, outputs in submission.items():
        if not isinstance(outputs, list):
            raise ValueError(f"{task_id}: outputs are not a list")
        for index, item in enumerate(outputs):
            if not isinstance(item, dict) or set(item) != {"attempt_1", "attempt_2"}:
                raise ValueError(f"{task_id}[{index}]: expected exactly attempt_1 and attempt_2")
            for name in ("attempt_1", "attempt_2"):
                grid = item[name]
                if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
                    raise ValueError(f"{task_id}[{index}].{name}: invalid grid")
            output_count += 1
    return len(submission), output_count


def normalize_row(row: dict[str, str]) -> dict[str, str]:
    return {
        "".join(character.lower() for character in key if character.isalnum()): value
        for key, value in row.items()
        if key
    }


def parse_csv(text: str) -> list[dict[str, str]]:
    try:
        return [normalize_row(row) for row in csv.DictReader(text.splitlines())]
    except Exception:
        return []


def first_value(row: dict[str, str] | None, *keys: str) -> str | None:
    if not row:
        return None
    for key in keys:
        normalized = "".join(character.lower() for character in key if character.isalnum())
        value = row.get(normalized)
        if value is not None and str(value).strip() not in {"", "None", "null", "nan"}:
            return str(value).strip()
    return None


def parse_number(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def refresh_score_and_rank(record: dict[str, Any], *, wait_seconds: int = 1200) -> None:
    deadline = time.time() + wait_seconds
    submission_text = ""
    entered_text = ""
    while True:
        submissions = run(
            ["kaggle", "competitions", "submissions", COMPETITION, "-v", "-q"],
            timeout=180,
        )
        entered = run(
            ["kaggle", "competitions", "list", "--group", "entered", "-v"],
            timeout=180,
        )
        submission_text = submissions["output"]
        entered_text = entered["output"]
        rows = parse_csv(submission_text)
        latest = rows[0] if rows else None
        score = first_value(latest, "publicScore", "public score", "score")
        rank = None
        teams = None
        for row in parse_csv(entered_text):
            if first_value(row, "ref", "competition", "id") == COMPETITION:
                rank = first_value(row, "userRank", "user rank", "rank")
                teams = first_value(row, "teamCount", "team count", "teams")
                break
        if score is not None and rank not in (None, "0"):
            break
        if time.time() >= deadline:
            break
        time.sleep(30)

    (LOG_DIR / "06_submissions.csv").write_text(submission_text, encoding="utf-8")
    (LOG_DIR / "07_entered_competitions.csv").write_text(entered_text, encoding="utf-8")
    rows = parse_csv(submission_text)
    latest = rows[0] if rows else None
    record["submission_status"] = first_value(latest, "status") or record.get("submission_status")
    record["public_score"] = parse_number(
        first_value(latest, "publicScore", "public score", "score")
    )
    record["private_score"] = parse_number(first_value(latest, "privateScore", "private score"))
    for row in parse_csv(entered_text):
        if first_value(row, "ref", "competition", "id") == COMPETITION:
            rank_value = parse_number(first_value(row, "userRank", "user rank", "rank"))
            teams_value = parse_number(first_value(row, "teamCount", "team count", "teams"))
            record["public_rank"] = int(rank_value) if rank_value is not None else None
            record["team_count"] = int(teams_value) if teams_value is not None else None
            break


def refresh_existing_pending(existing: dict[str, Any]) -> int:
    token = os.environ.get("KAGGLE_API_TOKEN", "").strip() or os.environ.get("KAGGLE_KEY", "").strip()
    username = os.environ.get("KAGGLE_USERNAME", "").strip()
    if not username or not token:
        existing.update(
            state="BLOCKED_AUTH",
            error="Kaggle authentication is required to refresh the pending submission.",
            interpretation="A previous kernel/submission record exists, but its score and rank cannot be refreshed without Kaggle authentication.",
        )
        write_records(existing)
        return 0
    refresh_score_and_rank(existing, wait_seconds=900)
    score = existing.get("public_score")
    if score is None:
        existing["state"] = "SUBMITTED_SCORE_PENDING"
        existing["interpretation"] = "Kaggle still has not exposed a public score for the exact frozen kernel version."
    elif score > 0:
        existing["state"] = "SCORED_NONZERO"
        existing["interpretation"] = "The frozen v3 artifact achieved a nonzero visible Kaggle score. Cycle 001 is terminal."
    else:
        existing["state"] = "SCORED_NULL"
        existing["interpretation"] = "The frozen v3 artifact received a visible score of zero. Cycle 001 is terminal."
    existing["error"] = None
    write_records(existing)
    return 0


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    existing = load_existing()
    if existing and existing.get("state") in TERMINAL_STATES:
        print(f"Cycle 001 already has terminal state {existing['state']}; no second submission will be made.")
        return 0
    if existing and existing.get("submission_ref") and existing.get("state") == "SUBMITTED_SCORE_PENDING":
        return refresh_existing_pending(existing)

    username = os.environ.get("KAGGLE_USERNAME", "").strip()
    api_token = os.environ.get("KAGGLE_API_TOKEN", "").strip()
    legacy_key = os.environ.get("KAGGLE_KEY", "").strip()
    record = initial_record(username)

    try:
        materialize_frozen_source(record)
    except Exception as exc:
        record.update(
            state="SOURCE_FREEZE_ERROR",
            error=str(exc),
            interpretation="The registered frozen source could not be materialized; no Kaggle action was attempted.",
        )
        write_records(record)
        return 0

    if not username or not (api_token or legacy_key):
        missing = []
        if not username:
            missing.append("KAGGLE_USERNAME")
        if not (api_token or legacy_key):
            missing.append("KAGGLE_API_TOKEN or legacy KAGGLE_KEY")
        record.update(
            state="BLOCKED_AUTH",
            error="Missing GitHub Actions secret(s): " + ", ".join(missing),
            interpretation="The exact self-contained notebook is prepared and hashed, but no authenticated Kaggle submission or rank exists.",
        )
        write_records(record)
        return 0

    write_kernel_metadata(username)
    kernel_ref = record["kernel_ref"]

    preflight = run(
        ["kaggle", "competitions", "files", COMPETITION, "--page-size", "1", "-q"],
        timeout=180,
    )
    log_command("01_preflight.txt", preflight, record)
    if preflight["returncode"] != 0:
        record.update(
            state="BLOCKED_RULES_OR_AUTH",
            error=tail(preflight["output"]),
            interpretation="Kaggle authentication failed or the account has not joined the competition and accepted its rules. No submission or rank exists.",
        )
        write_records(record)
        return 0

    push = run(
        ["kaggle", "kernels", "push", "-p", str(KERNEL_DIR), "-t", "3600"],
        timeout=3900,
    )
    log_command("02_kernel_push.txt", push, record)
    if push["returncode"] != 0:
        record.update(
            state="KERNEL_PUSH_FAILED",
            error=tail(push["output"]),
            interpretation="Kaggle rejected the self-contained frozen kernel before competition submission.",
        )
        write_records(record)
        return 0

    version = parse_kernel_version(push["output"])
    record["kernel_version"] = version
    if version is None:
        record.update(
            state="KERNEL_VERSION_UNRESOLVED",
            error="The official CLI did not expose a parseable kernel version in its push output.",
            interpretation="No code-competition submission was made because the immutable kernel version could not be named safely.",
        )
        write_records(record)
        return 0

    if not wait_for_kernel(kernel_ref, record):
        record.update(
            state="KERNEL_EXECUTION_FAILED",
            interpretation="The frozen Kaggle notebook did not complete successfully; no code-competition submission was made.",
        )
        write_records(record)
        return 0

    output_dir = RESULT_DIR / "kernel_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    kernel_output = run(
        ["kaggle", "kernels", "output", kernel_ref, "-p", str(output_dir), "-o", "-q"],
        timeout=600,
    )
    log_command("04_kernel_output.txt", kernel_output, record)
    submission_path = output_dir / "submission.json"
    if kernel_output["returncode"] != 0 or not submission_path.is_file():
        record.update(
            state="KERNEL_OUTPUT_FAILED",
            error=tail(kernel_output["output"]) or "submission.json was not produced",
            interpretation="The exact kernel version completed without a retrievable submission.json; no competition submission was made.",
        )
        write_records(record)
        return 0

    try:
        task_count, output_count = validate_submission(submission_path)
    except Exception as exc:
        record.update(
            state="SUBMISSION_VALIDATION_FAILED",
            error=str(exc),
            interpretation="The kernel output violated the frozen two-attempt contract; no competition submission was made.",
        )
        write_records(record)
        return 0
    record["hidden_task_count"] = task_count
    record["hidden_output_count"] = output_count
    record["submission_sha256"] = sha256(submission_path)

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
            f"Frozen representation v3 — Private Cycle 001 — {FROZEN_COMMIT[:12]}",
            "--wait",
            "10800",
            "--poll-interval",
            "30",
        ],
        timeout=10900,
    )
    log_command("05_competition_submit.txt", submit, record)
    ref_match = re.search(r"(?i)submission\s+ref:\s*(\d+)", submit["output"])
    if ref_match:
        record["submission_ref"] = ref_match.group(1)

    refresh_score_and_rank(record, wait_seconds=1200)
    score = record.get("public_score")
    status_text = str(record.get("submission_status") or "").lower()
    if score is not None and score > 0:
        record.update(
            state="SCORED_NONZERO",
            error=None,
            interpretation="The frozen v3 artifact achieved a nonzero visible Kaggle score. This is the immutable terminal Cycle 001 result.",
        )
    elif score == 0:
        record.update(
            state="SCORED_NULL",
            error=None,
            interpretation="The frozen v3 artifact scored zero on the visible Kaggle leaderboard. The null result is preserved and Cycle 002 requires a new registration.",
        )
    elif submit["returncode"] == 0 or record.get("submission_ref"):
        record.update(
            state="SUBMITTED_SCORE_PENDING",
            error=None,
            interpretation="Kaggle accepted the exact frozen kernel version, but a visible score or rank was not yet available when the record was written.",
        )
    else:
        record.update(
            state="SUBMISSION_FAILED_OR_TIMED_OUT",
            error=tail(submit["output"]),
            interpretation="Kaggle did not return a completed scored submission. The frozen kernel, version, output hash, and logs are preserved.",
        )
    if any(token in status_text for token in ("error", "invalid", "failed")):
        record["state"] = "SUBMISSION_ERROR"
        record["error"] = record.get("error") or record.get("submission_status")
    write_records(record)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
