"""`gads auth login|status` -- one-time OAuth2 setup for non-interactive use."""

from __future__ import annotations

import typer

from googleadscli import client_factory, config, formatting
from googleadscli.commands._common import run_guarded

app = typer.Typer(no_args_is_help=True, help="OAuth2 setup and credential check")

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
        help="Optional: not needed under cloud-managed access without a classic developer token",
    ),
    login_customer_id: str = typer.Option(
        None, "--login-customer-id", help="Optional MCC CID to use as the default login-customer-id"
    ),
    no_browser: bool = typer.Option(
        False, "--no-browser", help="Print the auth URL instead of opening a browser (for SSH/remote sessions)"
    ),
) -> None:
    """Runs the interactive OAuth2 consent flow once and stores the refresh token."""

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
        help="Path to the service-account JSON key file from the Google Cloud Console",
    ),
    developer_token: str = typer.Option(
        None,
        "--developer-token",
        envvar="GOOGLE_ADS_DEVELOPER_TOKEN",
        help="Optional: not needed under cloud-managed access without a classic developer token",
    ),
    impersonated_email: str = typer.Option(
        None,
        "--impersonated-email",
        help="Only for domain-wide delegation: the Workspace user to impersonate. "
        "Not needed if the key file's client_email has been added directly as a user "
        "on the Google Ads account/MCC.",
    ),
    login_customer_id: str = typer.Option(None, "--login-customer-id", help="Optional MCC CID"),
) -> None:
    """Sets up service-account-based authentication (no interactive consent needed).

    Prerequisite: the client_email from the JSON key file must be added as a
    user with the appropriate access level on the Google Ads account (or MCC)
    (Tools & Settings > Access and Security > Users), unless domain-wide
    delegation is used instead via --impersonated-email.
    """

    def _run() -> None:
        import json as _json
        from pathlib import Path

        key_path = Path(json_key_file_path).expanduser().resolve()
        if not key_path.exists():
            raise config.ConfigError(f"Service account key file not found: {key_path}")
        key_data = _json.loads(key_path.read_text(encoding="utf-8"))
        if key_data.get("type") != "service_account":
            raise config.ConfigError(
                f"File {key_path} is not a service-account key (type={key_data.get('type')!r})."
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
                "hint": "Make sure this client_email has been added as a user on the Google Ads "
                "account, unless --impersonated-email was set.",
            },
            fmt=ctx.obj["format"],
        )

    run_guarded(ctx, _run)


@app.command("status")
def status(ctx: typer.Context) -> None:
    """Checks the current configuration against the real API (list_accessible_customers)."""

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
