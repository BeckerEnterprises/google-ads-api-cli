"""`gads query` -- generische GAQL-Ausfuehrung."""

from __future__ import annotations

import typer

from googleadscli import formatting, gaql
from googleadscli.commands import _common
from googleadscli.utils import normalize_customer_id


def register(app: typer.Typer) -> None:
    @app.command("query")
    def query_cmd(
        ctx: typer.Context,
        customer_id: str = typer.Option(..., "--customer-id", "-c", help="Google Ads Customer ID (CID)"),
        gaql_query: str = typer.Option(..., "--gaql", "-q", help="GAQL-Query-String"),
        paged: bool = typer.Option(
            False, "--paged", help="search/SearchPager statt search_stream verwenden"
        ),
    ) -> None:
        """Fuehrt eine beliebige GAQL-Abfrage aus (Reporting/Lesen)."""

        def _run() -> None:
            client = _common.build_client(ctx)
            rows = gaql.run_query(
                client,
                normalize_customer_id(customer_id),
                gaql_query,
                paged=paged,
                version=ctx.obj["version"],
            )
            formatting.render(rows, fmt=ctx.obj["format"])

        _common.run_guarded(ctx, _run)
