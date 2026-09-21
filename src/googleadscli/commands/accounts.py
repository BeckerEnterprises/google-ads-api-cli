"""`gads accounts list-hierarchy` -- list MCC account hierarchy / CIDs.

Thin convenience wrapper: the Google Ads API's `customer_client` resource
already returns the full direct and indirect account hierarchy of a manager
account (MCC) in a single GAQL query.
"""

from __future__ import annotations

import typer

from googleadscli import formatting, gaql
from googleadscli.commands import _common
from googleadscli.utils import normalize_customer_id

app = typer.Typer(no_args_is_help=True, help="Account hierarchy / CIDs under an MCC")

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
    customer_id: str = typer.Option(
        ..., "--customer-id", "-c", help="CID of the (manager) account to list from"
    ),
) -> None:
    """Lists all direct and indirect client CIDs under an MCC account."""

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
