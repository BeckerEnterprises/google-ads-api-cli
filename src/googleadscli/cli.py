"""Root Typer app: global options, error handling, subcommand registration."""

from __future__ import annotations

import typer

from googleadscli.commands import accounts, auth, call, fields, highlevel, mutate, query

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Full-featured CLI for the Google Ads API (v25) -- built for AI agents.",
)


@app.callback()
def main_callback(
    ctx: typer.Context,
    config: str = typer.Option(
        None, "--config", envvar="GOOGLE_ADS_CONFIGURATION_FILE_PATH", help="Path to google-ads.yaml"
    ),
    api_version: str = typer.Option("v25", "--api-version", help="Google Ads API version"),
    output_format: str = typer.Option("json", "--format", help="Output format: json|table|csv"),
    developer_token: str = typer.Option(None, "--developer-token", envvar="GOOGLE_ADS_DEVELOPER_TOKEN"),
    client_id: str = typer.Option(None, "--client-id", envvar="GOOGLE_ADS_CLIENT_ID"),
    client_secret: str = typer.Option(None, "--client-secret", envvar="GOOGLE_ADS_CLIENT_SECRET"),
    refresh_token: str = typer.Option(None, "--refresh-token", envvar="GOOGLE_ADS_REFRESH_TOKEN"),
    json_key_file_path: str = typer.Option(
        None,
        "--json-key-file-path",
        envvar="GOOGLE_ADS_JSON_KEY_FILE_PATH",
        help="Path to a service-account JSON key file (alternative to the OAuth flow)",
    ),
    impersonated_email: str = typer.Option(
        None,
        "--impersonated-email",
        envvar="GOOGLE_ADS_IMPERSONATED_EMAIL",
        help="Only for domain-wide delegation: the Workspace user to impersonate",
    ),
    use_adc: bool = typer.Option(
        False,
        "--use-adc",
        envvar="GOOGLE_ADS_USE_APPLICATION_DEFAULT_CREDENTIALS",
        help="Use Application Default Credentials instead of explicit credentials",
    ),
    login_customer_id: str = typer.Option(None, "--login-customer-id", envvar="GOOGLE_ADS_LOGIN_CUSTOMER_ID"),
    debug: bool = typer.Option(False, "--debug", help="Show full tracebacks instead of structured errors"),
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


app.add_typer(auth.app, name="auth", help="OAuth2 setup and credential check")
app.add_typer(accounts.app, name="accounts", help="Account hierarchy / CIDs under an MCC")
app.add_typer(highlevel.app, name="hl", help="Convenience commands for common workflows")
app.add_typer(fields.app, name="fields", help="Look up API field metadata")
query.register(app)
mutate.register(app)
call.register(app)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
