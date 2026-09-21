"""Ausgabeformatierung: json (Standard, agentenfreundlich), table, csv."""

from __future__ import annotations

import csv
import json
import sys
from typing import Any


def _flatten(d: dict, parent_key: str = "") -> dict:
    items: dict[str, Any] = {}
    for key, value in d.items():
        full_key = f"{parent_key}.{key}" if parent_key else key
        if isinstance(value, dict):
            items.update(_flatten(value, full_key))
        else:
            items[full_key] = value
    return items


def render(data: Any, *, fmt: str = "json") -> None:
    if fmt == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
        return

    rows = data if isinstance(data, list) else [data]
    flat_rows = [_flatten(row) if isinstance(row, dict) else {"value": row} for row in rows]

    if fmt == "csv":
        if not flat_rows:
            return
        fieldnames = list({key for row in flat_rows for key in row})
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flat_rows)
        return

    if fmt == "table":
        from rich.console import Console
        from rich.table import Table

        if not flat_rows:
            print("(keine Ergebnisse)")
            return
        fieldnames = list({key for row in flat_rows for key in row})
        table = Table(show_header=True, header_style="bold")
        for name in fieldnames:
            table.add_column(name)
        for row in flat_rows:
            table.add_row(*(str(row.get(name, "")) for name in fieldnames))
        Console().print(table)
        return

    raise ValueError(f"Unbekanntes Ausgabeformat: {fmt}")
