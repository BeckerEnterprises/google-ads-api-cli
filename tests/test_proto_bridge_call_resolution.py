"""Tests fuer den generischen `call`-Fallback-Bridge (beliebiger Service/Methode)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from googleadscli import proto_bridge as pb


def test_resolve_call_target_finds_method(fake_client):
    _service, method, request_cls = pb.resolve_call_target(
        fake_client, "GoogleAdsFieldService", "get_google_ads_field", version="v25"
    )
    assert method.__name__ == "get_google_ads_field"
    assert request_cls.__name__ == "GetGoogleAdsFieldRequest"


def test_resolve_call_target_unknown_service_raises(fake_client):
    with pytest.raises(pb.BridgeError):
        pb.resolve_call_target(fake_client, "NotAService", "whatever", version="v25")


def test_resolve_call_target_unknown_method_raises(fake_client):
    with pytest.raises(pb.BridgeError):
        pb.resolve_call_target(fake_client, "CampaignService", "not_a_real_method", version="v25")


def test_invoke_call_roundtrips_json(fake_client):
    from google.ads.googleads.v25.resources.types.google_ads_field import GoogleAdsField
    from google.ads.googleads.v25.services.services.google_ads_field_service.client import (
        GoogleAdsFieldServiceClient,
    )

    fake_field = GoogleAdsField(name="campaign.id", category="ATTRIBUTE", data_type="INT64", selectable=True)

    with patch.object(
        GoogleAdsFieldServiceClient, "get_google_ads_field", autospec=True, return_value=fake_field
    ):
        result = pb.invoke_call(
            fake_client,
            "GoogleAdsFieldService",
            "get_google_ads_field",
            {"resource_name": "googleAdsFields/campaign.id"},
            version="v25",
        )

    assert result == {
        "name": "campaign.id",
        "category": "ATTRIBUTE",
        "data_type": "INT64",
        "selectable": True,
    }


def test_invoke_call_flattens_search_stream_batches(fake_client):
    from google.ads.googleads.v25.services.services.google_ads_service.client import (
        GoogleAdsServiceClient,
    )
    from google.ads.googleads.v25.services.types.google_ads_service import (
        GoogleAdsRow,
        SearchGoogleAdsStreamResponse,
    )

    batch_1 = SearchGoogleAdsStreamResponse(results=[GoogleAdsRow(campaign={"id": 1})])
    batch_2 = SearchGoogleAdsStreamResponse(results=[GoogleAdsRow(campaign={"id": 2})])

    with patch.object(
        GoogleAdsServiceClient, "search_stream", autospec=True, return_value=iter([batch_1, batch_2])
    ):
        result = pb.invoke_call(
            fake_client,
            "GoogleAdsService",
            "search_stream",
            {"customer_id": "123", "query": "SELECT campaign.id FROM campaign"},
            version="v25",
        )

    assert result == [{"campaign": {"id": "1"}}, {"campaign": {"id": "2"}}]


def test_list_service_names_includes_known_services():
    names = pb.list_service_names(version="v25")
    assert "CampaignService" in names
    assert "BatchJobService" in names
    assert "ServiceService" not in names  # keine doppelten "Service"-Suffixe


def test_list_service_methods(fake_client):
    methods = pb.list_service_methods(fake_client, "CampaignService", version="v25")
    assert "mutate_campaigns" in methods
