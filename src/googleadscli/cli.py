"""Root Typer-App: globale Optionen, Fehlerbehandlung, Subcommand-Registrierung."""

from __future__ import annotations

import typer

from googleadscli.commands import accounts, auth, call, highlevel, mutate, query

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Vollumfaengliche CLI fuer die Google Ads API (v25) -- fuer KI-Agenten.",
)


@app.callback()
def main_callback(
    ctx: typer.Context,
    config: str = typer.Option(
        None, "--config", envvar="GOOGLE_ADS_CONFIGURATION_FILE_PATH", help="Pfad zur google-ads.yaml"
    ),
    api_version: str = typer.Option("v25", "--api-version", help="Google Ads API Version"),
    output_format: str = typer.Option("json", "--format", help="Ausgabeformat: json|table|csv"),
    developer_token: str = typer.Option(None, "--developer-token", envvar="GOOGLE_ADS_DEVELOPER_TOKEN"),
    client_id: str = typer.Option(None, "--client-id", envvar="GOOGLE_ADS_CLIENT_ID"),
    client_secret: str = typer.Option(None, "--client-secret", envvar="GOOGLE_ADS_CLIENT_SECRET"),
    refresh_token: str = typer.Option(None, "--refresh-token", envvar="GOOGLE_ADS_REFRESH_TOKEN"),
    json_key_file_path: str = typer.Option(
        None,
        "--json-key-file-path",
        envvar="GOOGLE_ADS_JSON_KEY_FILE_PATH",
        help="Pfad zu einer Service-Account-JSON-Schluesseldatei (Alternative zum OAuth-Flow)",
    ),
    impersonated_email: str = typer.Option(
        None,
        "--impersonated-email",
        envvar="GOOGLE_ADS_IMPERSONATED_EMAIL",
        help="Nur fuer Domain-Wide-Delegation: zu impersonierender Workspace-Nutzer",
    ),
    use_adc: bool = typer.Option(
        False,
        "--use-adc",
        envvar="GOOGLE_ADS_USE_APPLICATION_DEFAULT_CREDENTIALS",
        help="Application Default Credentials verwenden statt expliziter Zugangsdaten",
    ),
    login_customer_id: str = typer.Option(None, "--login-customer-id", envvar="GOOGLE_ADS_LOGIN_CUSTOMER_ID"),
    debug: bool = typer.Option(False, "--debug", help="Vollstaendige Tracebacks statt strukturierter Fehler"),
) -> None:
    ctx.obj = {
        "config_path": config,
        "version": api_version,
        "format": output_format,
        "debug": debug,
        "cli_overrides": {
            "developer_token": developer_token,
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "json_key_file_path": json_key_file_path,
            "impersonated_email": impersonated_email,
            "use_application_default_credentials": use_adc or None,
            "login_customer_id": login_customer_id,
        },
    }


app.add_typer(auth.app, name="auth", help="OAuth2-Einrichtung und Zugangspruefung")
app.add_typer(accounts.app, name="accounts", help="Kontohierarchie / CIDs unter einem MCC")
app.add_typer(highlevel.app, name="hl", help="Komfortbefehle fuer haeufige Workflows")
query.register(app)
mutate.register(app)
call.register(app)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
