"""Gemeinsame Test-Fixtures.

Die Konstruktion eines GoogleAdsClient (auch nur zum Zweck der Reflection ueber
Service-/Message-Klassen) loest normalerweise einen echten OAuth-Refresh-Call
aus (siehe google.ads.googleads.oauth2). Da Reflection und JSON<->Proto-
Konvertierung selbst komplett offline funktionieren, wird hier lediglich der
Credentials-Refresh no-op gepatcht -- alle weiteren Tests laufen ohne
Netzwerkzugriff gegen echte generierte Protobuf-/GAPIC-Klassen.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def fake_client():
    from unittest.mock import patch

    from google.oauth2.credentials import Credentials

    with patch.object(Credentials, "refresh", lambda self, request: None):
        from google.ads.googleads.client import GoogleAdsClient

        yield GoogleAdsClient.load_from_dict(
            {
                "developer_token": "fake_dev_token",
                "client_id": "fake_client_id",
                "client_secret": "fake_client_secret",
                "refresh_token": "fake_refresh_token",
                "use_proto_plus": True,
            },
            version="v25",
        )
