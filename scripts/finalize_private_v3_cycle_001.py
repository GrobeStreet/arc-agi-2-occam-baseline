#!/usr/bin/env python3
"""Create the sanitized, immutable result record for private v3 Cycle 001."""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


COMPETITION = "arc-prize-2026-arc-agi-2"


def normalize_key(value: str) -> str:
    return "".join(character.lower() for character in value if character.isalnum())


def normalized_row(row: dict[str, str]) -> dict[str, str]:
    return {normalize_key(key): value for key, value in row.items() if key is not None}


def read_csv(path: Path | None) -> list[dict[str, str]]:
    if path is None or not path.is_file() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [normalized_row(row) for row in csv.DictReader(handle)]


def first_value(row: dict[str, str] | None, *keys: str) -> str | None:
    if not row:
        return None
    for key in keys:
        value = row.get(normalize_key(key))
        if value is not None and str(value).strip() not in {"", "None", "null", "nan"}:
            return str(value).strip()
    return None


def numeric(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def find_competition(rows: list[dict[str, str]]) -> dict[str, str] | None:
    for row in rows:
        reference = first_value(row, "ref", "competition", "id")
        if reference == COMPETITION:
            return row
    return None


def infer_state(
    override: str | None,
    submission_status: str | None,
    public_score: float | None,
) -> str:
    if override:
        return override
    status = (submission_status or "").lower()
    if any(token in status for token in ("error", "fail", "invalid")):
        return "SUBMISSION_ERROR"
    if public_score is None:
        return "SUBMITTED_SCORE_PENDING"
    if public_score > 0:
        return "NONZERO_TEST_SUCCESS"
    return "NULL"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="results/private_v3_cycle_001")
    parser.add_argument("--source-manifest")
    parser.add_argument("--submissions-csv")
    parser.add_argument("--competitions-csv")
    parser.add_argument("--kernel-id")
    parser.add_argument("--kernel-version")
    parser.add_argument("--workflow-state")
    parser.add_argument("--detail")
    parser.add_argument("--workflow-url")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    source_manifest: dict[str, Any] = {}
    if args.source_manifest:
        manifest_path = Path(args.source_manifest)
        if manifest_path.is_file():
            source_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    submission_rows = read_csv(Path(args.submissions_csv) if args.submissions_csv else None)
    latest_submission = submission_rows[0] if submission_rows else None
    competition_rows = read_csv(Path(args.competitions_csv) if args.competitions_csv else None)
    competition_row = find_competition(competition_rows)

    submission_status = first_value(latest_submission, "status")
    public_score_text = first_value(
        latest_submission, "publicScore", "public score", "score"
    )
    private_score_text = first_value(latest_submission, "privateScore", "private score")
    public_score = numeric(public_score_text)
    private_score = numeric(private_score_text)
    public_rank_text = first_value(competition_row, "userRank", "user rank", "rank")
    team_count_text = first_value(competition_row, "teamCount", "team count", "teams")
    public_rank = int(float(public_rank_text)) if numeric(public_rank_text) is not None else None
    team_count = int(float(team_count_text)) if numeric(team_count_text) is not None else None

    state = infer_state(args.workflow_state, submission_status, public_score)
    timestamp = datetime.now(timezone.utc).isoformat()

    record = {
        "cycle": "private-v3-cycle-001",
        "competition": COMPETITION,
        "state": state,
        "recorded_at_utc": timestamp,
        "kernel_id": args.kernel_id,
        "kernel_version": int(args.kernel_version) if args.kernel_version else None,
        "submission_status": submission_status,
        "public_score": public_score,
        "private_score": private_score,
        "public_rank": public_rank,
        "team_count": team_count,
        "detail": args.detail,
        "workflow_url": args.workflow_url,
        "registration": "HYPOTHESIS-private-v3-cycle-001.md",
        "source_manifest": source_manifest,
        "claim_boundary": (
            "Public leaderboard score/rank during the competition is not the final private "
            "leaderboard result. No rank exists when the state is blocked or score-pending."
        ),
    }

    (output_dir / "status.json").write_text(
        json.dumps(record, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )

    def display(value: Any, suffix: str = "") -> str:
        return "not available" if value is None else f"{value}{suffix}"

    lines = [
        "# Private Cycle 001 — Frozen V3 Kaggle Result",
        "",
        f"**State:** `{state}`  ",
        f"**Competition:** `{COMPETITION}`  ",
        f"**Recorded:** {timestamp}",
        "",
        "## Official Kaggle record",
        "",
        f"- Kernel: `{args.kernel_id or 'not created'}`",
        f"- Kernel version: {display(record['kernel_version'])}",
        f"- Submission status: {display(submission_status)}",
        f"- Visible public score: {display(public_score)}",
        f"- Visible public rank: {display(public_rank)}",
        f"- Teams in competition snapshot: {display(team_count)}",
        f"- Final private score: {display(private_score)}",
        "",
        "## Interpretation",
        "",
    ]
    if state == "BLOCKED_MISSING_KAGGLE_AUTH":
        lines.append(
            "The frozen notebook package is ready, but the GitHub runner did not receive "
            "authenticated Kaggle credentials. No notebook was uploaded and no official rank exists."
        )
    elif state == "BLOCKED_COMPETITION_NOT_JOINED":
        lines.append(
            "Kaggle authentication succeeded, but the account has not joined the competition "
            "and accepted its rules. No official submission or rank exists."
        )
    elif state == "NONZERO_TEST_SUCCESS":
        lines.append(
            "The frozen v3 cycle achieved a nonzero visible Kaggle score. This is the terminal "
            "aggregate result for Cycle 001; representation changes require a new registration."
        )
    elif state == "NULL":
        lines.append(
            "The frozen v3 cycle received a visible score of zero. This null result is retained; "
            "representation changes require a new registration."
        )
    elif state == "SUBMITTED_SCORE_PENDING":
        lines.append(
            "The code-competition notebook was submitted, but Kaggle had not returned a score "
            "when this record was written. The exact kernel version is preserved."
        )
    else:
        lines.append(
            "The workflow did not complete a normal scored submission. See `detail` and the "
            "workflow logs; the frozen solver remains unchanged."
        )

    lines.extend(
        [
            "",
            "## Representation firewall",
            "",
            "Do not modify the representation under Cycle 001. Any new work begins with a "
            "committed `HYPOTHESIS-representation-cycle-002.md` created from the inactive template.",
            "",
            f"Workflow: {args.workflow_url or 'not available'}",
        ]
    )
    (output_dir / "STATUS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
