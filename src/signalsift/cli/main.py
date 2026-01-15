"""Main CLI entry point for SignalSift."""

import click
from rich.console import Console

from signalsift import __version__
from signalsift.cli.cache import cache
from signalsift.cli.keywords import keywords
from signalsift.cli.report import report
from signalsift.cli.scan import scan
from signalsift.cli.sources import sources
from signalsift.cli.status import status
from signalsift.database.connection import database_exists, initialize_database
from signalsift.utils.logging import setup_logging

console = Console()


@click.group()
@click.version_option(__version__, prog_name="signalsift")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """
    SignalSift - Competitive intelligence for the SEOForge ecosystem.

    Scrapes Reddit and YouTube for SEO insights, caches content,
    and generates reports for Claude AI brainstorming sessions.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    # Set up logging
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(level=log_level)

    # Initialize database if needed
    if not database_exists():
        console.print("[dim]Initializing database...[/dim]")
        initialize_database(populate_defaults=True)
        console.print("[green]✓[/green] Database initialized with default sources and keywords")


@cli.command()
@click.pass_context
def init(ctx: click.Context) -> None:
    """Initialize or reinitialize the database with defaults."""
    from signalsift.database.connection import reset_database

    if database_exists():
        if not click.confirm(
            "Database already exists. This will reset all data. Continue?"
        ):
            console.print("[yellow]Cancelled.[/yellow]")
            return

        reset_database()
        console.print("[green]✓[/green] Database reset with default configuration")
    else:
        initialize_database(populate_defaults=True)
        console.print("[green]✓[/green] Database initialized with default sources and keywords")


# Register command groups
cli.add_command(scan)
cli.add_command(report)
cli.add_command(status)
cli.add_command(sources)
cli.add_command(keywords)
cli.add_command(cache)


if __name__ == "__main__":
    cli()
