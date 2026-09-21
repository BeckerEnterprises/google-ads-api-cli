"""Tests for `gads fields list|show` (GoogleAdsFieldService wrapper)."""

from __future__ import annotations

import json
from unittest.mock import patch

from typer.testing import CliRunner

from googleadscli.cli import app

runner = CliRunner()


def test_fields_list_builds_prefix_query_and_returns_rows(fake_client):
    from google.ads.googleads.v25.resources.types.google_ads_field import GoogleAdsField
    from google.ads.googleads.v25.services.services.google_ads_field_service.client import (
        GoogleAdsFieldServiceClient,
    )

    fake_field = GoogleAdsField(name="ad_group.status", category="ATTRIBUTE", data_type="ENUM", selectable=True)

    with patch("googleadscli.commands._common.build_client", return_value=fake_client), patch.object(
        GoogleAdsFieldServiceClient, "search_google_ads_fields", autospec=True, return_value=[fake_field]
    ) as mocked:
        result = runner.invoke(app, ["fields", "list", "ad_group"])

    assert result.exit_code == 0, result.output
    rows = json.loads(result.output)
    assert rows == [{"name": "ad_group.status", "category": "ATTRIBUTE", "data_type": "ENUM", "selectable": True}]
    sent_query = mocked.call_args.kwargs["request"].query
    assert 'name LIKE "ad_group.%"' in sent_query
    assert "OR" not in sent_query


def test_fields_list_with_category_filter(fake_client):
    from google.ads.googleads.v25.services.services.google_ads_field_service.client import (
        GoogleAdsFieldServiceClient,
    )

    with patch("googleadscli.commands._common.build_client", return_value=fake_client), patch.object(
        GoogleAdsFieldServiceClient, "search_google_ads_fields", autospec=True, return_value=[]
    ) as mocked:
        result = runner.invoke(app, ["fields", "list", "ad_group", "--category", "metric"])

    assert result.exit_code == 0, result.output
    sent_query = mocked.call_args.kwargs["request"].query
    assert 'category = "METRIC"' in sent_query


def test_fields_show_exact_lookup(fake_client):
    from google.ads.googleads.v25.resources.types.google_ads_field import GoogleAdsField
    from google.ads.googleads.v25.services.services.google_ads_field_service.client import (
        GoogleAdsFieldServiceClient,
    )

    fake_field = GoogleAdsField(name="ad_group.status", category="ATTRIBUTE")

    with patch("googleadscli.commands._common.build_client", return_value=fake_client), patch.object(
        GoogleAdsFieldServiceClient, "search_google_ads_fields", autospec=True, return_value=[fake_field]
    ) as mocked:
        result = runner.invoke(app, ["fields", "show", "ad_group.status"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["name"] == "ad_group.status"
    assert 'name = "ad_group.status"' in mocked.call_args.kwargs["request"].query


def test_fields_show_no_match_returns_empty_object(fake_client):
    from google.ads.googleads.v25.services.services.google_ads_field_service.client import (
        GoogleAdsFieldServiceClient,
    )

    with patch("googleadscli.commands._common.build_client", return_value=fake_client), patch.object(
        GoogleAdsFieldServiceClient, "search_google_ads_fields", autospec=True, return_value=[]
    ):
        result = runner.invoke(app, ["fields", "show", "not.a.real.field"])

    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {}
