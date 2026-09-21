"""Executes arbitrary GAQL queries via GoogleAdsService."""

from __future__ import annotations

from googleadscli.proto_bridge import DEFAULT_VERSION, message_to_dict


def run_query(
    client,
    customer_id: str,
    gaql: str,
    *,
    paged: bool = False,
    version: str = DEFAULT_VERSION,
) -> list[dict]:
    """Runs a GAQL query and returns a flat list of row dicts.

    Default: GoogleAdsService.search_stream (batches are merged into one flat
    list). With paged=True, search/SearchPager is used instead
    (compatibility/debugging option).
    """
    service = client.get_service("GoogleAdsService", version=version)
    rows: list[dict] = []

    if paged:
        request_cls = type(client.get_type("SearchGoogleAdsRequest", version=version))
        request = request_cls(customer_id=customer_id, query=gaql)
        for row in service.search(request=request):
            rows.append(message_to_dict(row))
        return rows

    request_cls = type(client.get_type("SearchGoogleAdsStreamRequest", version=version))
    request = request_cls(customer_id=customer_id, query=gaql)
    for batch in service.search_stream(request=request):
        for row in batch.results:
            rows.append(message_to_dict(row))
    return rows
