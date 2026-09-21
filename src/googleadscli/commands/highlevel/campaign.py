"""`gads hl campaign create|pause|enable|remove` -- Kampagnen verwalten."""

from __future__ import annotations

import typer

from googleadscli import formatting, proto_bridge
from googleadscli.commands import _common
from googleadscli.utils import normalize_customer_id

app = typer.Typer(no_args_is_help=True, help="Kampagnen anlegen/verwalten")


@app.command("create")
def create(
    ctx: typer.Context,
    customer_id: str = typer.Option(..., "--customer-id", "-c"),
    name: str = typer.Option(..., "--name"),
    budget_resource_name: str = typer.Option(..., "--budget", help="Resource-Name des CampaignBudget"),
    advertising_channel_type: str = typer.Option("SEARCH", "--channel-type", help="z.B. SEARCH, DISPLAY, PERFORMANCE_MAX"),
    status: str = typer.Option("PAUSED", "--status", help="Standard PAUSED, um versehentliche Ausgaben zu vermeiden"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    def _run() -> None:
        client = _common.build_client(ctx)
        operations = [
            {
                "create": {
                    "name": name,
                    "campaign_budget": budget_resource_name,
                    "advertising_channel_type": advertising_channel_type,
                    "status": status,
                }
            }
        ]
        result = proto_bridge.run_mutate(
            client,
            "campaign",
            normalize_customer_id(customer_id),
            operations,
            validate_only=dry_run,
            version=ctx.obj["version"],
        )
        formatting.render(result, fmt=ctx.obj["format"])

    _common.run_guarded(ctx, _run)


def _set_status(ctx: typer.Context, customer_id: str, resource_name: str, status: str, dry_run: bool) -> None:
    def _run() -> None:
        client = _common.build_client(ctx)
        operations = [{"update": {"resource_name": resource_name, "status": status}}]
        result = proto_bridge.run_mutate(
            client,
            "campaign",
            normalize_customer_id(customer_id),
            operations,
            validate_only=dry_run,
            version=ctx.obj["version"],
        )
        formatting.render(result, fmt=ctx.obj["format"])

    _common.run_guarded(ctx, _run)


@app.command("pause")
def pause(
    ctx: typer.Context,
    customer_id: str = typer.Option(..., "--customer-id", "-c"),
    resource_name: str = typer.Argument(..., help="Resource-Name der Kampagne"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    _set_status(ctx, customer_id, resource_name, "PAUSED", dry_run)


@app.command("enable")
def enable(
    ctx: typer.Context,
    customer_id: str = typer.Option(..., "--customer-id", "-c"),
    resource_name: str = typer.Argument(..., help="Resource-Name der Kampagne"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    _set_status(ctx, customer_id, resource_name, "ENABLED", dry_run)


@app.command("remove")
def remove(
    ctx: typer.Context,
    customer_id: str = typer.Option(..., "--customer-id", "-c"),
    resource_name: str = typer.Argument(..., help="Resource-Name der Kampagne"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    def _run() -> None:
        client = _common.build_client(ctx)
        operations = [{"remove": resource_name}]
        result = proto_bridge.run_mutate(
            client,
            "campaign",
            normalize_customer_id(customer_id),
            operations,
            validate_only=dry_run,
            version=ctx.obj["version"],
        )
        formatting.render(result, fmt=ctx.obj["format"])

    _common.run_guarded(ctx, _run)
