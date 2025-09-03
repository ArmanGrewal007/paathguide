#!/usr/bin/env python3
"""
Test script for the enhanced fuzzy search with text cleaning.
"""

from pathlib import Path
import sys

# Add the paathguide package to the path
sys.path.insert(0, str(Path(__file__).parent))

from paathguide.db.models import Verse, create_database, get_session
from paathguide.fuzzy_search import SGGSFuzzySearcher
from paathguide.text_cleaner import WhisperTextCleaner


def create_sample_data():
    """Create some sample verses for testing."""
    create_database()
    session = get_session()

    # Add sample verses including the correct one
    sample_verses = [
        {
            "gurmukhi": "ਤੁਮਹੇ ਛਾਡਿ ਕੋਈ ਅਵਰ ਨ ਧਿਆਊਂ",
            "english": "Except for You, I do not meditate on any other.",
            "page": 404,
            "line": 5,
        },
        {
            "gurmukhi": "ਰਾਮ ਨਾਮ ਬਿਨ ਤਿਲੁ ਨ ਤ੍ਰਪਤੇ",
            "english": "Without the Lord's Name, they are not satisfied, even for an instant.",
            "page": 284,
            "line": 3,
        },
        {
            "gurmukhi": "ਸਰਬ ਧਰਮ ਮਹਿ ਸ੍ਰੇਸਟ ਧਰਮੁ",
            "english": "Of all dharmas, the highest dharma",
            "page": 1298,
            "line": 7,
        },
        {
            "gurmukhi": "ਆਪੇ ਹੀ ਸਭ ਕਿਛੁ ਦੇਖਿਆ",
            "english": "He Himself sees all things.",
            "page": 932,
            "line": 12,
        },
    ]

    for verse_data in sample_verses:
        verse = Verse(**verse_data)
        session.add(verse)

    session.commit()
    session.close()

    print("Sample data created successfully!")


def test_fuzzy_search():
    """Test the fuzzy search with the STT example."""
    print("Testing fuzzy search with STT example...")
    print("=" * 60)

    # Initialize searcher with database session
    session = get_session()
    searcher = SGGSFuzzySearcher(session)

    # Your STT example
    stt_output = "ਤੁਮੇ ਛਾਡ ਕੋਈ ਅਵਰ ਨਾਤ੍ਯਾਂ"

    print(f"STT Output: {stt_output}")
    print("\nTesting different cleaning approaches:")
    print("-" * 40)

    # Compare different cleaning approaches
    comparison = searcher.compare_cleaning_approaches(stt_output, limit=2, score_cutoff=20.0)

    for approach, data in comparison.items():
        print(f"\n{approach.upper()}:")
        print(f"  Cleaned query: {data['cleaned_query']}")
        print(f"  Results ({len(data['results'])}):")

        for i, result in enumerate(data["results"], 1):
            print(f"    {i}. Score: {result.score:.1f} - {result.verse.gurmukhi}")
            print(f"       Page {result.verse.page}, Line {result.verse.line}")

    print("\n" + "=" * 60)
    print("Individual text cleaner tests:")
    print("-" * 40)

    cleaner = WhisperTextCleaner()

    print(f"Original STT: {stt_output}")
    print(f"Basic clean:  {cleaner.clean_stt_output(stt_output, aggressive=False)}")
    print(f"Aggressive:   {cleaner.clean_stt_output(stt_output, aggressive=True)}")
    print(f"For matching: {cleaner.clean_for_matching(stt_output)}")

    # Test against the correct verse
    correct_verse = "ਤੁਮਹੇ ਛਾਡਿ ਕੋਈ ਅਵਰ ਨ ਧਿਆਊਂ"
    print(f"\nTarget verse: {correct_verse}")
    print(f"Target clean: {cleaner.clean_for_matching(correct_verse)}")

    # Test similarity scores
    from rapidfuzz import fuzz

    print("\nSimilarity scores:")
    print(f"Raw texts: {fuzz.WRatio(stt_output, correct_verse):.1f}")
    print(f"Cleaned:   {fuzz.WRatio(cleaner.clean_for_matching(stt_output), cleaner.clean_for_matching(correct_verse)):.1f}")

    session.close()


if __name__ == "__main__":
    # Check if database exists
    db_path = Path("sggs.db")
    if db_path.exists():
        print("Database exists, removing for fresh test...")
        db_path.unlink()

    create_sample_data()
    test_fuzzy_search()
