"""Simple test script to verify the SGGS API functionality."""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paathguide import schemas
from paathguide.data_loader import load_sample_data
from paathguide.models import SessionLocal, create_tables
from paathguide.repository import VerseRepository


def test_basic_functionality():
    """Test basic database operations."""
    print("🧪 Testing SGGS API functionality...")

    # Create tables
    create_tables()
    print("✅ Database tables created")

    # Get database session
    db = SessionLocal()

    try:
        # Load sample data
        load_sample_data(db)
        print("✅ Sample data loaded")

        # Test repository operations
        repo = VerseRepository(db)

        # Test getting all verses
        verses = repo.get_verses(limit=5)
        print(f"✅ Retrieved {len(verses)} verses")

        # Test search
        search_query = schemas.VerseSearchQuery(query="ਸਚੁ", page_number=None, raag=None, author=None, limit=5, offset=0)
        search_results, total = repo.search_verses(search_query)
        print(f"✅ Search found {total} results")

        # Test page content
        page_verses = repo.get_page_content(1)
        print(f"✅ Page 1 has {len(page_verses)} verses")

        # Test statistics
        stats = repo.get_stats()
        print(f"✅ Database stats: {stats.total_verses} total verses")

        # Test random verse
        random_verse = repo.get_random_verse()
        if random_verse:
            print(f"✅ Random verse: {random_verse.gurmukhi_text[:50]}...")

        print("\n🎉 All tests passed! The API is ready to use.")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        db.close()

    return True


if __name__ == "__main__":
    test_basic_functionality()
