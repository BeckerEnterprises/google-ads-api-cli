"""`gads hl budget create` -- CampaignBudget anlegen."""

from __future__ import annotations

import typer

from googleadscli import formatting, proto_bridge
from googleadscli.commands import _common
from googleadscli.utils import normalize_customer_id

app = typer.Typer(no_args_is_help=True, help="CampaignBudget anlegen/verwalten")


@app.command("create")
def create(
    ctx: typer.Context,
    customer_id: str = typer.Option(..., "--customer-id", "-c"),
    name: str = typer.Option(..., "--name"),
    amount_micros: int = typer.Option(..., "--amount-micros", help="Tagesbudget in Micros (1 EUR = 1_000_000)"),
    delivery_method: str = typer.Option("STANDARD", "--delivery-method", help="STANDARD|ACCELERATED"),
    explicitly_shared: bool = typer.Option(False, "--explicitly-shared"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    def _run() -> None:
        client = _common.build_client(ctx)
        operations = [
            {
                "create": {
                    "name": name,
                    "amount_micros": amount_micros,
                    "delivery_method": delivery_method,
                    "explicitly_shared": explicitly_shared,
                }
            }
        ]
        result = proto_bridge.run_mutate(
            client,
            "campaign_budget",
            normalize_customer_id(customer_id),
            operations,
            validate_only=dry_run,
            version=ctx.obj["version"],
        )
        formatting.render(result, fmt=ctx.obj["format"])

    _common.run_guarded(ctx, _run)
