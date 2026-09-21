"""Gemeinsame Hilfsfunktionen fuer Subcommands: Fehler-Guard, Client-Aufbau."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import typer

from googleadscli import client_factory, errors


def build_client(ctx: typer.Context):
    obj = ctx.obj
    return client_factory.build_client(
        config_path=obj["config_path"],
        cli_overrides=obj["cli_overrides"],
        version=obj["version"],
    )


def run_guarded(ctx: typer.Context, fn: Callable[[], Any]) -> Any:
    try:
        return fn()
    except Exception as exc:  # strukturierte Fehlerausgabe statt rohem Traceback
        errors.handle_exception(exc, debug=ctx.obj.get("debug", False))
