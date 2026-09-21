"""`gads accounts list-hierarchy` -- MCC-Kontohierarchie / CIDs auflisten.

Duenner Komfort-Wrapper: die Google Ads API liefert ueber die `customer_client`-
Ressource bereits die gesamte direkte und indirekte Kontohierarchie eines
Manager-Kontos (MCC) in einer einzigen GAQL-Abfrage.
"""

from __future__ import annotations

import typer

from googleadscli import formatting, gaql
from googleadscli.commands import _common
from googleadscli.utils import normalize_customer_id

app = typer.Typer(no_args_is_help=True, help="Kontohierarchie / CIDs unter einem MCC")

_HIERARCHY_QUERY = """
SELECT
  customer_client.client_customer,
  customer_client.level,
  customer_client.manager,
  customer_client.descriptive_name,
  customer_client.currency_code,
  customer_client.time_zone,
  customer_client.status
FROM customer_client
WHERE customer_client.status = 'ENABLED'
"""


@app.command("list-hierarchy")
def list_hierarchy(
    ctx: typer.Context,
    customer_id: str = typer.Option(..., "--customer-id", "-c", help="CID des (Manager-)Kontos, ab dem gelistet wird"),
) -> None:
    """Listet alle direkten und indirekten Kunden-CIDs unter einem MCC-Konto."""

    def _run() -> None:
        client = _common.build_client(ctx)
        rows = gaql.run_query(
            client,
            normalize_customer_id(customer_id),
            _HIERARCHY_QUERY,
            version=ctx.obj["version"],
        )
        formatting.render(rows, fmt=ctx.obj["format"])

    _common.run_guarded(ctx, _run)
