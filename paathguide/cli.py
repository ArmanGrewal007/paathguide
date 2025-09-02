"""Command-line interface for managing SGGS data."""

import click

from paathguide.data_loader import SGGSDataLoader, load_sample_data
from paathguide.db_helper.models import SessionLocal, create_tables


@click.group()
def cli():
    """SGGS Database Management CLI"""
    pass


@cli.command()
@click.option("--file-path", "-f", required=True, help="Path to SGGS DOCX file")
@click.option("--skip-first", "-s", default=2, help="Number of initial lines to skip")
@click.option("--clear/--no-clear", default=False, help="Clear existing data before loading")
def load_data(file_path: str, skip_first: int, clear: bool):
    """Load SGGS data from DOCX file."""
    create_tables()

    db = SessionLocal()
    try:
        loader = SGGSDataLoader(db)

        if clear:
            click.echo("Clearing existing data...")
            loader.clear_database()

        click.echo(f"Loading data from {file_path}...")
        count = loader.load_from_docx(file_path, skip_first)
        click.echo(f"✅ Successfully loaded {count} verses")

    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        db.close()


@cli.command()
def load_sample():
    """Load sample data for testing."""
    create_tables()

    db = SessionLocal()
    try:
        click.echo("Loading sample data...")
        load_sample_data(db)
        click.echo("✅ Sample data loaded successfully")
    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        db.close()


@cli.command()
def clear_data():
    """Clear all data from the database."""
    if click.confirm("Are you sure you want to clear all data?"):
        db = SessionLocal()
        try:
            loader = SGGSDataLoader(db)
            loader.clear_database()
            click.echo("✅ Database cleared successfully")
        except Exception as e:
            click.echo(f"❌ Error: {e}")
        finally:
            db.close()


@cli.command()
def init_db():
    """Initialize the database (create tables)."""
    create_tables()
    click.echo("✅ Database initialized successfully")


@cli.command()
def stats():
    """Show database statistics."""
    from .repository import VerseRepository

    db = SessionLocal()
    try:
        repo = VerseRepository(db)
        stats = repo.get_stats()

        click.echo("\n📊 SGGS Database Statistics:")
        click.echo(f"Total verses: {stats.total_verses}")
        click.echo(f"Total pages: {stats.total_pages}")
        click.echo(f"Verses with translations: {stats.verses_with_translations}")
        click.echo(f"Verses with transliterations: {stats.verses_with_transliterations}")
        click.echo(f"Unique raags: {stats.unique_raags}")
        click.echo(f"Unique authors: {stats.unique_authors}")

    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    cli()
