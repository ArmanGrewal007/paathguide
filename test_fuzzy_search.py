#!/usr/bin/env python3
"""
Test script for the enhanced fuzzy search with text cleaning.
"""

import os
import sys
from pathlib import Path

# Add the paathguide package to the path
sys.path.insert(0, str(Path(__file__).parent / "paathguide"))

from paathguide.db_helper.models import Verse, create_database, get_session
from paathguide.fuzzy_search import SGGSFuzzySearcher
from paathguide.text_cleaner import SGGSTextCleaner

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
            "line": 5
        },
        {
            "gurmukhi": "ਰਾਮ ਨਾਮ ਬਿਨ ਤਿਲੁ ਨ ਤ੍ਰਪਤੇ",
            "english": "Without the Lord's Name, they are not satisfied, even for an instant.",
            "page": 284,
            "line": 3
        },
        {
            "gurmukhi": "ਸਰਬ ਧਰਮ ਮਹਿ ਸ੍ਰੇਸਟ ਧਰਮੁ",
            "english": "Of all dharmas, the highest dharma",
            "page": 1298,
            "line": 7
        },
        {
            "gurmukhi": "ਆਪੇ ਹੀ ਸਭ ਕਿਛੁ ਦੇਖਿਆ",
            "english": "He Himself sees all things.",
            "page": 932,
            "line": 12
        }
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
    
    searcher = SGGSFuzzySearcher()
    
    # Your STT example
        query_text = "ਗੁਰ ਪੱੱਾਦ ਜਾਪ ਆਦ ਸਾਚ ਜਗਾਦ ਸਾਚ ਹਿ ਸਾਚ ਨਾਨਕ ਹੋ ਸੀਬੀ ਸਾਚ ਸਚ਼ਿ ਸ਼ਿ ਸ਼ਿ ਸ਼ਿ ਸ਼ਿ"
        
        print(f"\n🎯 Query: {query_text}")
        print(f"📏 Query length: {len(query_text)} characters")
        
        # Test best match
        print("\n1️⃣ Finding best match...")
        best_match = fuzzy_searcher.find_best_match(query_text, score_cutoff=30.0)
        
        if best_match:
            print(f"✅ Best match found!")
            print(f"   Score: {best_match.score:.1f}%")
            print(f"   Method: {best_match.ratio_type}")
            print(f"   Text: {best_match.verse.gurmukhi_text}")
            print(f"   Page: {best_match.verse.page_number}, Line: {best_match.verse.line_number}")
        else:
            print("❌ No match found above threshold")
        
        # Test multiple matches
        print("\n2️⃣ Finding multiple matches...")
        matches = fuzzy_searcher.find_closest_matches(query_text, limit=3, score_cutoff=20.0)
        
        if matches:
            print(f"✅ Found {len(matches)} matches:")
            for i, match in enumerate(matches, 1):
                print(f"   {i}. Score: {match.score:.1f}% - {match.verse.gurmukhi_text[:50]}...")
        else:
            print("❌ No matches found")
        
        # Test with preprocessing
        print("\n3️⃣ Testing with text preprocessing...")
        preprocessed_matches = fuzzy_searcher.search_with_preprocessing(
            query_text, limit=3, score_cutoff=20.0
        )
        
        if preprocessed_matches:
            print(f"✅ Found {len(preprocessed_matches)} matches with preprocessing:")
            for i, match in enumerate(preprocessed_matches, 1):
                print(f"   {i}. Score: {match.score:.1f}% - {match.verse.gurmukhi_text[:50]}...")
        
        # Test comparison of methods
        print("\n4️⃣ Comparing different fuzzy methods...")
        comparison = fuzzy_searcher.compare_with_multiple_methods(
            query_text, limit=2, score_cutoff=15.0
        )
        
        for method, results in comparison.items():
            if results:
                best = results[0]
                print(f"   {method}: {best.score:.1f}% - {best.verse.gurmukhi_text[:30]}...")
            else:
                print(f"   {method}: No matches")
        
        # Test individual text comparison
        print("\n5️⃣ Testing direct text comparison...")
        sample_verse = "ਆਦਿ ਸਚੁ ਜੁਗਾਦਿ ਸਚੁ"
        similarity = fuzzy_searcher.get_similarity_score(query_text, sample_verse)
        print(f"   Similarity with '{sample_verse}': {similarity:.1f}%")
        
        print("\n🎉 Fuzzy search tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    test_fuzzy_search()
