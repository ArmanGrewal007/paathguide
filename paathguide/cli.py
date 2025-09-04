"""Command-line interface for managing SGGS data."""

import click

from paathguide.db.data_loader import SGGSDataLoader
from paathguide.db.models import SessionLocal, create_tables


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

        # count = loader.load_from_docx_line_by_line(file_path, skip_first)
        count = loader.load_by_page(file_path, skip_first)
        click.echo(f"✅ Successfully loaded {count} verses")

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
def rebuild_fts():
    """Rebuild the FTS5 search index."""
    from paathguide.db.data_loader import SGGSDataLoader
    
    db = SessionLocal()
    try:
        loader = SGGSDataLoader(db)
        loader.rebuild_fts_index()
        click.echo("✅ FTS5 index rebuilt successfully")
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
    from .db.repository import SGGSTextRepository

    db = SessionLocal()
    try:
        repo = SGGSTextRepository(db)
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


@cli.command()
@click.option("--query", "-q", required=True, help="Search query text")
@click.option("--limit", "-l", default=5, help="Number of results to show")
def search(query: str, limit: int):
    """Test FTS5 search functionality."""
    from paathguide.db.repository import SGGSTextRepository
    from paathguide.db.schemas import VerseSearchQuery

    db = SessionLocal()
    try:
        repo = SGGSTextRepository(db)
        search_query = VerseSearchQuery(query=query, limit=limit, offset=0)
        verses, total = repo.search_sggs_texts(search_query)
        
        click.echo(f"\n🔍 Search results for '{query}' (showing {len(verses)} of {total} total):")
        click.echo("=" * 80)
        
        for i, verse in enumerate(verses, 1):
            click.echo(f"\n{i}. ID: {verse.id}")
            if verse.page_number is not None:
                page_line = f"Page {verse.page_number}"
                if verse.line_number is not None:
                    page_line += f", Line {verse.line_number}"
                click.echo(f"   Location: {page_line}")
            click.echo(f"   Text: {verse.gurmukhi_text[:100]}...")
            if verse.raag is not None:
                click.echo(f"   Raag: {verse.raag}")
            if verse.author is not None:
                click.echo(f"   Author: {verse.author}")

    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        db.close()


@cli.command()
@click.option("--query", "-q", required=True, help="Raw whisper transcription")
@click.option("--limit", "-l", default=5, help="Number of results to show")
@click.option("--min-similarity", "-s", default=0.3, help="Minimum similarity threshold")
def fuzzy_search(query: str, limit: int, min_similarity: float):
    """Search using whisper output with automatic cleaning and fuzzy matching."""
    from paathguide.search.fuzzy_search import FuzzySearch

    try:
        with FuzzySearch() as searcher:
            # Show cleaned query
            cleaned = searcher.get_cleaned_query(query)
            click.echo(f"Original: '{query}'")
            click.echo(f"Cleaned:  '{cleaned}'")
            
            # Perform search with fuzzy enabled
            results, total = searcher.search(query, limit, use_fuzzy=True, min_similarity=min_similarity)
            
            click.echo(f"\n🔍 Found {total} results (showing {len(results)}):")
            click.echo("=" * 60)
            
            for i, result in enumerate(results, 1):
                click.echo(f"\n{i}. Page {result.page_number}")
                click.echo(f"   Text: {result.gurmukhi_text[:100]}...")
                if result.raag is not None:
                    click.echo(f"   Raag: {result.raag}")

    except Exception as e:
        click.echo(f"❌ Error: {e}")


@cli.command()
def add_test_data():
    """Add some test data to verify FTS5 functionality."""
    from paathguide.db.repository import SGGSTextRepository
    from paathguide.db.schemas import VerseSearchQuery, SGGSTextCreate

    db = SessionLocal()
    try:
        repo = SGGSTextRepository(db)
        
        # Add some test verses
        test_verses = [
            SGGSTextCreate(
                gurmukhi_text="ਆਦਿ ਸਚੁ ਜੁਗਾਦਿ ਸਚੁ ॥",
                page_number=1,
                line_number=1,
                raag="ਜਪੁਜੀ ਸਾਹਿਬ",
                author="ਗੁਰੂ ਨਾਨਕ ਦੇਵ ਜੀ"
            ),
            SGGSTextCreate(
                gurmukhi_text="ਹੈ ਭੀ ਸਚੁ ਨਾਨਕ ਹੋਸੀ ਭੀ ਸਚੁ ॥੧॥",
                page_number=1,
                line_number=2,
                raag="ਜਪੁਜੀ ਸਾਹਿਬ",
                author="ਗੁਰੂ ਨਾਨਕ ਦੇਵ ਜੀ"
            ),
            SGGSTextCreate(
                gurmukhi_text="ਸੋਚੈ ਸੋਚਿ ਨ ਹੋਵਈ ਜੇ ਸੋਚੀ ਲਖ ਵਾਰ ॥",
                page_number=1,
                line_number=3,
                raag="ਜਪੁਜੀ ਸਾਹਿਬ",
                author="ਗੁਰੂ ਨਾਨਕ ਦੇਵ ਜੀ"
            ),
        ]
        
        for verse in test_verses:
            repo.create_sggs_text(verse)
        
        click.echo(f"✅ Added {len(test_verses)} test verses")
        
        # Test search
        click.echo("\n🧪 Testing FTS5 search...")
        search_query = VerseSearchQuery(query="ਸਚੁ", limit=5, offset=0)
        results, total = repo.search_sggs_texts(search_query)
        
        click.echo(f"Search for 'ਸਚੁ' returned {total} results")
        for result in results:
            click.echo(f"  - {result.gurmukhi_text}")

    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    cli()
