"""Small helper functions."""

from __future__ import annotations

import json
from pathlib import Path


def normalize_customer_id(customer_id: str) -> str:
    """Strips hyphens from a CID input like '123-456-7890'."""
    return customer_id.replace("-", "").strip()


def load_json_arg(value: str | None) -> dict | list | None:
    """Loads JSON from either a literal string, or, if value is an existing
    file path (with an '@' prefix), from that file."""
    if value is None:
        return None
    if value.startswith("@"):
        path = Path(value[1:]).expanduser()
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(value)
