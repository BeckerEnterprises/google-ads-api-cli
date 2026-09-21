"""End-to-end test of the `gads query` command via the Typer CLI."""

from __future__ import annotations

import json
from unittest.mock import patch

from typer.testing import CliRunner

from googleadscli.cli import app

runner = CliRunner()


def test_query_command_outputs_json_rows(fake_client):
    from google.ads.googleads.v25.services.services.google_ads_service.client import (
        GoogleAdsServiceClient,
    )
    from google.ads.googleads.v25.services.types.google_ads_service import (
        GoogleAdsRow,
        SearchGoogleAdsStreamResponse,
    )

    batch = SearchGoogleAdsStreamResponse(results=[GoogleAdsRow(campaign={"id": 42, "name": "My Campaign"})])

    with patch("googleadscli.commands._common.build_client", return_value=fake_client), patch.object(
        GoogleAdsServiceClient, "search_stream", autospec=True, return_value=iter([batch])
    ):
        result = runner.invoke(
            app,
            ["query", "--customer-id", "123-456-7890", "--gaql", "SELECT campaign.id FROM campaign"],
        )

    assert result.exit_code == 0, result.output
    rows = json.loads(result.output)
    assert rows == [{"campaign": {"id": "42", "name": "My Campaign"}}]
