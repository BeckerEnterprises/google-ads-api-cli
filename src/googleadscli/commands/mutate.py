"""`gads mutate <resource>` -- generic create/update/remove for any resource."""

from __future__ import annotations

import typer

from googleadscli import formatting, proto_bridge
from googleadscli.commands import _common
from googleadscli.utils import load_json_arg, normalize_customer_id


def register(app: typer.Typer) -> None:
    @app.command("mutate")
    def mutate_cmd(
        ctx: typer.Context,
        resource: str = typer.Argument(
            ..., help="Resource key in snake_case, e.g. 'campaign', 'ad_group_criterion'"
        ),
        customer_id: str = typer.Option(..., "--customer-id", "-c"),
        operations_json: str = typer.Option(
            ...,
            "--operations-json",
            "-o",
            help="JSON array of operations ({'create'|'update'|'remove': ...}); "
            "load from a file with '@path.json'",
        ),
        dry_run: bool = typer.Option(
            False, "--dry-run", help="validate_only: only validate, don't change anything"
        ),
        partial_failure: bool = typer.Option(
            False, "--partial-failure", help="Don't fail the whole request if individual operations fail"
        ),
    ) -> None:
        """Runs create/update/remove operations for a resource."""

        def _run() -> None:
            operations = load_json_arg(operations_json)
            if not isinstance(operations, list):
                raise ValueError("--operations-json must be a JSON array of operations.")

            client = _common.build_client(ctx)
            result = proto_bridge.run_mutate(
                client,
                resource,
                normalize_customer_id(customer_id),
                operations,
                partial_failure=partial_failure,
                validate_only=dry_run,
                version=ctx.obj["version"],
            )
            formatting.render(result, fmt=ctx.obj["format"])

        _common.run_guarded(ctx, _run)
