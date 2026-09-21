"""Kleine Hilfsfunktionen."""

from __future__ import annotations

import json
from pathlib import Path


def normalize_customer_id(customer_id: str) -> str:
    """Entfernt Bindestriche aus einer CID-Eingabe wie '123-456-7890'."""
    return customer_id.replace("-", "").strip()


def load_json_arg(value: str | None) -> dict | list | None:
    """Laedt JSON entweder aus einem literalen String oder, falls value ein
    existierender Dateipfad ist (mit '@' Praefix), aus dieser Datei."""
    if value is None:
        return None
    if value.startswith("@"):
        path = Path(value[1:]).expanduser()
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(value)
