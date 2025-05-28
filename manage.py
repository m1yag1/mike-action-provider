"""Management script for the action provider."""
import click
from pathlib import Path

from sqlalchemy import text

from mike_action_provider.app import create_app
from mike_action_provider.db.connection import get_engine, init_db
from mike_action_provider.db.models import Base


@click.group()
def cli():
    """Management commands for the action provider."""
    pass


def _list_routes(app):
    """List all routes in the application.

    Args:
        app: Flask application instance.

    Returns:
        list: List of route information strings.
    """
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        output.append(f'{rule.endpoint} {methods} {rule.rule}')
    return output


@cli.command()
def list_routes():
    """List all routes in the application."""
    app = create_app()
    with app.test_request_context():
        routes = _list_routes(app)
        for route in routes:
            click.echo(route)


@cli.command()
def reset_db():
    """Reset the database by dropping all tables and recreating them.

    This will prompt for confirmation before proceeding.
    """
    engine = get_engine()
    db_path = Path(engine.url.database)

    if not db_path.exists():
        click.echo("Database does not exist. Creating new database...")
        init_db()
        return

    if not click.confirm(
        f"WARNING: This will delete all data in {db_path}. Are you sure?",
        default=False,
    ):
        click.echo("Operation cancelled.")
        return

    # Drop all tables
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = OFF"))
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.execute(text("PRAGMA foreign_keys = ON"))
        conn.commit()

    # Recreate tables
    init_db()
    click.echo("Database has been reset.")


if __name__ == "__main__":
    cli()
