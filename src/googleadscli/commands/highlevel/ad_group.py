"""`gads hl ad-group create` -- create an ad group."""

from __future__ import annotations

import typer

from googleadscli import formatting, proto_bridge
from googleadscli.commands import _common
from googleadscli.utils import normalize_customer_id

app = typer.Typer(no_args_is_help=True, help="Create/manage ad groups")


@app.command("create")
def create(
    ctx: typer.Context,
    customer_id: str = typer.Option(..., "--customer-id", "-c"),
    name: str = typer.Option(..., "--name"),
    campaign_resource_name: str = typer.Option(..., "--campaign", help="Resource name of the campaign"),
    status: str = typer.Option("PAUSED", "--status"),
    ad_group_type: str = typer.Option("SEARCH_STANDARD", "--type", help="AdGroupTypeEnum value"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    def _run() -> None:
        client = _common.build_client(ctx)
        operations = [
            {
                "create": {
                    "name": name,
                    "campaign": campaign_resource_name,
                    "status": status,
                    "type": ad_group_type,
                }
            }
        ]
        result = proto_bridge.run_mutate(
            client,
            "ad_group",
            normalize_customer_id(customer_id),
            operations,
            validate_only=dry_run,
            version=ctx.obj["version"],
        )
        formatting.render(result, fmt=ctx.obj["format"])

    _common.run_guarded(ctx, _run)
