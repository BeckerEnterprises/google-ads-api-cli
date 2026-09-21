"""`gads hl ad create-responsive-search-ad` -- create a responsive search ad."""

from __future__ import annotations

import typer

from googleadscli import formatting, proto_bridge
from googleadscli.commands import _common
from googleadscli.utils import normalize_customer_id

app = typer.Typer(no_args_is_help=True, help="Create/manage ads")


@app.command("create-responsive-search-ad")
def create_responsive_search_ad(
    ctx: typer.Context,
    customer_id: str = typer.Option(..., "--customer-id", "-c"),
    ad_group_resource_name: str = typer.Option(..., "--ad-group"),
    final_url: str = typer.Option(..., "--final-url"),
    headline: list[str] = typer.Option(..., "--headline", help="Can be given multiple times, 3+ recommended"),
    description: list[str] = typer.Option(..., "--description", help="Can be given multiple times, 2+ recommended"),
    status: str = typer.Option("PAUSED", "--status"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    def _run() -> None:
        client = _common.build_client(ctx)
        create_payload = {
            "ad_group": ad_group_resource_name,
            "status": status,
            "ad": {
                "final_urls": [final_url],
                "responsive_search_ad": {
                    "headlines": [{"text": h} for h in headline],
                    "descriptions": [{"text": d} for d in description],
                },
            },
        }
        operations = [{"create": create_payload}]
        result = proto_bridge.run_mutate(
            client,
            "ad_group_ad",
            normalize_customer_id(customer_id),
            operations,
            validate_only=dry_run,
            version=ctx.obj["version"],
        )
        formatting.render(result, fmt=ctx.obj["format"])

    _common.run_guarded(ctx, _run)
