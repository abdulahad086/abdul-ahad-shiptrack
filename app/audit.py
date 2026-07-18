import os
from datetime import datetime, timezone

from app.config import settings


def write_audit_line(action: str, details: dict[str, str | int]) -> None:
    # ISO-8601 UTC timestamp with offset, e.g. "2026-07-16T09:31:22.481000+00:00"
    timestamp = datetime.now(timezone.utc).isoformat()

    log_path = settings.AUDIT_LOG_PATH
    parent_dir = os.path.dirname(log_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    details_str = " ".join(f"{k}={v}" for k, v in details.items())
    line = f"{timestamp} | {action} | {details_str}\n"

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line)
