"""`gads auth login|status` -- einmalige OAuth2-Einrichtung fuer nicht-interaktive Nutzung."""

from __future__ import annotations

import typer

from googleadscli import client_factory, config, formatting
from googleadscli.commands._common import run_guarded

app = typer.Typer(no_args_is_help=True, help="OAuth2-Einrichtung und Zugangspruefung")

SCOPES = ["https://www.googleapis.com/auth/adwords"]


@app.command("login")
def login(
    ctx: typer.Context,
    client_id: str = typer.Option(..., "--client-id", envvar="GOOGLE_ADS_CLIENT_ID"),
    client_secret: str = typer.Option(..., "--client-secret", envvar="GOOGLE_ADS_CLIENT_SECRET"),
    developer_token: str = typer.Option(
        None,
        "--developer-token",
        envvar="GOOGLE_ADS_DEVELOPER_TOKEN",
        help="Optional: nicht noetig bei Cloud-managed Access ohne klassischen Developer Token",
    ),
    login_customer_id: str = typer.Option(
        None, "--login-customer-id", help="Optionale MCC-CID, die standardmaessig als login-customer-id gesetzt wird"
    ),
    no_browser: bool = typer.Option(
        False, "--no-browser", help="Auth-URL ausgeben statt Browser zu oeffnen (fuer SSH/Remote-Sessions)"
    ),
) -> None:
    """Fuehrt einmalig den interaktiven OAuth2-Consent-Flow aus und speichert den Refresh Token."""

    def _run() -> None:
        from google_auth_oauthlib.flow import InstalledAppFlow

        client_config = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }
        }
        flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
        credentials = flow.run_local_server(open_browser=not no_browser)

        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": credentials.refresh_token,
        }
        if developer_token:
            data["developer_token"] = developer_token
        if login_customer_id:
            data["login_customer_id"] = login_customer_id.replace("-", "")

        path = config.write_config_file(data)
        formatting.render({"status": "ok", "config_path": str(path)}, fmt=ctx.obj["format"])

    run_guarded(ctx, _run)


@app.command("use-service-account")
def use_service_account(
    ctx: typer.Context,
    json_key_file_path: str = typer.Option(
        ...,
        "--json-key-file-path",
        help="Pfad zur Service-Account-JSON-Schluesseldatei aus der Google Cloud Console",
    ),
    developer_token: str = typer.Option(
        None,
        "--developer-token",
        envvar="GOOGLE_ADS_DEVELOPER_TOKEN",
        help="Optional: nicht noetig bei Cloud-managed Access ohne klassischen Developer Token",
    ),
    impersonated_email: str = typer.Option(
        None,
        "--impersonated-email",
        help="Nur fuer Domain-Wide-Delegation: zu impersonierender Workspace-Nutzer. "
        "Nicht noetig, wenn die client_email der Schluesseldatei direkt als Nutzer auf dem "
        "Google-Ads-Konto/MCC hinterlegt wurde.",
    ),
    login_customer_id: str = typer.Option(None, "--login-customer-id", help="Optionale MCC-CID"),
) -> None:
    """Richtet Service-Account-basierte Authentifizierung ein (kein interaktiver Consent noetig).

    Voraussetzung: die client_email aus der JSON-Schluesseldatei muss auf dem
    Google-Ads-Konto (oder MCC) als Nutzer mit passendem Zugriffslevel hinterlegt sein
    (Tools & Einstellungen > Zugriff und Sicherheit > Nutzer), es sei denn, es wird
    stattdessen per --impersonated-email eine Domain-Wide-Delegation genutzt.
    """

    def _run() -> None:
        import json as _json
        from pathlib import Path

        key_path = Path(json_key_file_path).expanduser().resolve()
        if not key_path.exists():
            raise config.ConfigError(f"Service-Account-Schluesseldatei nicht gefunden: {key_path}")
        key_data = _json.loads(key_path.read_text(encoding="utf-8"))
        if key_data.get("type") != "service_account":
            raise config.ConfigError(
                f"Datei {key_path} ist kein Service-Account-Schluessel (type={key_data.get('type')!r})."
            )

        data: dict = {"json_key_file_path": str(key_path)}
        if developer_token:
            data["developer_token"] = developer_token
        if impersonated_email:
            data["impersonated_email"] = impersonated_email
        if login_customer_id:
            data["login_customer_id"] = login_customer_id.replace("-", "")

        path = config.write_config_file(data)
        formatting.render(
            {
                "status": "ok",
                "config_path": str(path),
                "service_account_email": key_data.get("client_email"),
                "hint": "Stelle sicher, dass diese client_email als Nutzer auf dem Google-Ads-Konto "
                "hinterlegt ist, falls --impersonated-email nicht gesetzt wurde.",
            },
            fmt=ctx.obj["format"],
        )

    run_guarded(ctx, _run)


@app.command("status")
def status(ctx: typer.Context) -> None:
    """Prueft die aktuelle Konfiguration gegen die echte API (list_accessible_customers)."""

    def _run() -> None:
        client = client_factory.build_client(
            config_path=ctx.obj["config_path"],
            cli_overrides=ctx.obj["cli_overrides"],
            version=ctx.obj["version"],
        )
        service = client.get_service("CustomerService", version=ctx.obj["version"])
        response = service.list_accessible_customers()
        formatting.render(
            {"status": "ok", "accessible_customers": list(response.resource_names)},
            fmt=ctx.obj["format"],
        )

    run_guarded(ctx, _run)
