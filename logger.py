from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LOG_PATH = Path("logs/pawpal_runs.jsonl")


def log_run(
    user_input: str,
    result_status: str,
    details: dict[str, Any],
    log_path: Path | None = None,
) -> None:
    """
    Append one agent run to a JSONL log file.

    The caller controls which details are logged. Do not include API keys,
    environment variables, or raw third-party credentials in details.
    """
    target_path = log_path or LOG_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_input": user_input,
        "status": result_status,
        "details": details,
    }

    with target_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")
