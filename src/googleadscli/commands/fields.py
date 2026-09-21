"""`gads fields <resource>` -- look up Google Ads API field metadata.

Thin convenience wrapper around GoogleAdsFieldService.SearchGoogleAdsFields (a
GAQL-like mini query language against the API's global field catalog, no
customer account needed). Answers questions like "which fields does ad_group
offer?" without having to hand-build the mini-query syntax.

Note: this metadata only tells you what's *selectable*/*filterable*/*sortable*
via GAQL -- not what's *writable* via `mutate`, or which
advertising_channel_type it's compatible with. That can only be discovered by
reading the resource proto (see README) or by actually trying it
(--dry-run).
"""

from __future__ import annotations

import typer

from googleadscli import formatting, proto_bridge
from googleadscli.commands import _common

app = typer.Typer(no_args_is_help=True, help="Look up API field metadata (no customer account needed)")

_DEFAULT_SELECT = "name, category, data_type, selectable, filterable, sortable, is_repeated, enum_values"


@app.command("list")
def list_fields(
    ctx: typer.Context,
    resource: str = typer.Argument(
        ..., help="Resource or field name/prefix, e.g. 'ad_group' or 'campaign.network_settings'"
    ),
    category: str = typer.Option(
        None,
        "--category",
        help="Only this category: RESOURCE|ATTRIBUTE|SEGMENT|METRIC (default: all)",
    ),
    exact: bool = typer.Option(
        False, "--exact", help="Look up the exact field name instead of a prefix search"
    ),
) -> None:
    """Lists field metadata (selectable/filterable/sortable/enum_values/...) for a prefix."""

    def _run() -> None:
        if exact:
            where = f'name = "{resource}"'
        else:
            # GoogleAdsFieldService's mini query language doesn't support OR,
            # so this only lists the child fields (prefix); the exact
            # resource entry itself can be fetched via 'gads fields show'.
            where = f'name LIKE "{resource}.%"'
        if category:
            where += f' AND category = "{category.upper()}"'

        query = f"SELECT {_DEFAULT_SELECT} WHERE {where}"

        client = _common.build_client(ctx)
        rows = proto_bridge.invoke_call(
            client,
            "GoogleAdsFieldService",
            "search_google_ads_fields",
            {"query": query},
            version=ctx.obj["version"],
        )
        formatting.render(rows, fmt=ctx.obj["format"])

    _common.run_guarded(ctx, _run)


@app.command("show")
def show_field(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Exact field or resource name, e.g. 'ad_group.status'"),
) -> None:
    """Shows the full metadata (incl. selectable_with) for exactly one field/resource name."""

    def _run() -> None:
        client = _common.build_client(ctx)
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

    _common.run_guarded(ctx, _run)
