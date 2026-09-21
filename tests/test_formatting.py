"""Tests for output formatting (json/table/csv)."""

from __future__ import annotations

import json

from googleadscli import formatting


def test_render_json_outputs_valid_json(capsys):
    formatting.render({"a": 1, "b": {"c": 2}}, fmt="json")
    out = capsys.readouterr().out
    assert json.loads(out) == {"a": 1, "b": {"c": 2}}


def test_render_csv_flattens_nested_dicts(capsys):
    rows = [{"campaign": {"id": "1", "name": "A"}}, {"campaign": {"id": "2", "name": "B"}}]
    formatting.render(rows, fmt="csv")
    out = capsys.readouterr().out
    lines = out.strip().splitlines()
    assert lines[0].strip() in {"campaign.id,campaign.name", "campaign.name,campaign.id"}
    assert len(lines) == 3


def test_render_csv_empty_list_prints_nothing(capsys):
    formatting.render([], fmt="csv")
    out = capsys.readouterr().out
    assert out == ""


def test_render_table_smoke(capsys):
    rows = [{"campaign": {"id": "1", "name": "A"}}]
    formatting.render(rows, fmt="table")
    out = capsys.readouterr().out
    assert "campaign.id" in out
    assert "campaign.name" in out


def test_render_unknown_format_raises():
    import pytest

    with pytest.raises(ValueError):
        formatting.render({}, fmt="xml")
