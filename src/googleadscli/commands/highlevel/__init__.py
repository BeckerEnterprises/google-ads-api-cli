"""Convenience commands for common workflows -- thin wrappers over `mutate`/`call`.

Completeness is already provided by the generic base commands (query/mutate/
call); these commands exist purely for ergonomics.
"""

from __future__ import annotations

import typer

from googleadscli.commands.highlevel import ad, ad_group, budget, campaign, keyword

app = typer.Typer(no_args_is_help=True, help="Convenience commands for common workflows")
app.add_typer(budget.app, name="budget")
app.add_typer(campaign.app, name="campaign")
app.add_typer(ad_group.app, name="ad-group")
app.add_typer(keyword.app, name="keyword")
app.add_typer(ad.app, name="ad")
