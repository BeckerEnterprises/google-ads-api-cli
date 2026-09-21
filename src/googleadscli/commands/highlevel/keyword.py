"""`gads hl keyword add` -- add a keyword as an AdGroupCriterion."""

from __future__ import annotations

import typer

from googleadscli import formatting, proto_bridge
from googleadscli.commands import _common
from googleadscli.utils import normalize_customer_id

app = typer.Typer(no_args_is_help=True, help="Add/manage keywords")


@app.command("add")
def add(
    ctx: typer.Context,
    customer_id: str = typer.Option(..., "--customer-id", "-c"),
    ad_group_resource_name: str = typer.Option(..., "--ad-group", help="Resource name of the ad group"),
    text: str = typer.Option(..., "--text", help="Keyword text"),
    match_type: str = typer.Option("BROAD", "--match-type", help="EXACT|PHRASE|BROAD"),
    status: str = typer.Option("ENABLED", "--status"),
    cpc_bid_micros: int = typer.Option(None, "--cpc-bid-micros"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    def _run() -> None:
        client = _common.build_client(ctx)
        create_payload: dict = {
            "ad_group": ad_group_resource_name,
            "status": status,
            "keyword": {"text": text, "match_type": match_type},
        }
        if cpc_bid_micros is not None:
            create_payload["cpc_bid_micros"] = cpc_bid_micros

        operations = [{"create": create_payload}]
        result = proto_bridge.run_mutate(
            client,
            "ad_group_criterion",
            normalize_customer_id(customer_id),
            operations,
            validate_only=dry_run,
            version=ctx.obj["version"],
        )
        formatting.render(result, fmt=ctx.obj["format"])

    _common.run_guarded(ctx, _run)
