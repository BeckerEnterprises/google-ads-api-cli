"""`gads fields <resource>` -- Feld-Metadaten der Google Ads API nachschlagen.

Duenner Komfort-Wrapper um GoogleAdsFieldService.SearchGoogleAdsFields (eine
GAQL-aehnliche Mini-Query-Sprache gegen den globalen Feld-Katalog der API,
kein Kundenkonto noetig). Beantwortet Fragen wie "welche Felder bietet
ad_group?" ohne dass man die Mini-Query-Syntax von Hand bauen muss.

Hinweis: Diese Metadaten sagen nur, was *selectable*/*filterable*/*sortable*
per GAQL ist -- nicht, was per `mutate` *schreibbar* oder mit welchem
advertising_channel_type kompatibel ist. Das laesst sich nur durch Lesen des
Resource-Protos (siehe README) oder durch tatsaechliches Ausprobieren
(--dry-run) herausfinden.
"""

from __future__ import annotations

import typer

from googleadscli import formatting, proto_bridge
from googleadscli.commands._common import build_client, run_guarded

app = typer.Typer(no_args_is_help=True, help="Feld-Metadaten der API nachschlagen (kein Kundenkonto noetig)")

_DEFAULT_SELECT = "name, category, data_type, selectable, filterable, sortable, is_repeated, enum_values"


@app.command("list")
def list_fields(
    ctx: typer.Context,
    resource: str = typer.Argument(
        ..., help="Ressourcen- oder Feldname bzw. -praefix, z.B. 'ad_group' oder 'campaign.network_settings'"
    ),
    category: str = typer.Option(
        None,
        "--category",
        help="Nur diese Kategorie: RESOURCE|ATTRIBUTE|SEGMENT|METRIC (Default: alle)",
    ),
    exact: bool = typer.Option(
        False, "--exact", help="Nur exakten Feldnamen nachschlagen statt Praefix-Suche"
    ),
) -> None:
    """Listet Feld-Metadaten (selectable/filterable/sortable/enum_values/...) fuer ein Praefix."""

    def _run() -> None:
        if exact:
            where = f'name = "{resource}"'
        else:
            # Die Mini-Query-Sprache von GoogleAdsFieldService kennt kein OR,
            # daher listet dies nur die Kindfelder (Praefix); der exakte
            # Ressourcen-Eintrag selbst laesst sich per 'gads fields show' holen.
            where = f'name LIKE "{resource}.%"'
        if category:
            where += f' AND category = "{category.upper()}"'

        query = f"SELECT {_DEFAULT_SELECT} WHERE {where}"

        client = build_client(ctx)
        rows = proto_bridge.invoke_call(
            client,
            "GoogleAdsFieldService",
            "search_google_ads_fields",
            {"query": query},
            version=ctx.obj["version"],
        )
        formatting.render(rows, fmt=ctx.obj["format"])

    run_guarded(ctx, _run)


@app.command("show")
def show_field(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Exakter Feld- oder Ressourcenname, z.B. 'ad_group.status'"),
) -> None:
    """Zeigt die vollstaendigen Metadaten (inkl. selectable_with) fuer genau einen Feld-/Ressourcennamen."""

    def _run() -> None:
        client = build_client(ctx)
        rows = proto_bridge.invoke_call(
            client,
            "GoogleAdsFieldService",
            "search_google_ads_fields",
            {
                "query": (
                    "SELECT name, category, data_type, selectable, filterable, sortable, "
                    "is_repeated, enum_values, selectable_with, attribute_resources, metrics, segments "
                    f'WHERE name = "{name}"'
                )
            },
            version=ctx.obj["version"],
        )
        formatting.render(rows[0] if rows else {}, fmt=ctx.obj["format"])

    run_guarded(ctx, _run)
