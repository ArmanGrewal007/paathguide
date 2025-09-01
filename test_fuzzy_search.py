"""Test script for fuzzy search functionality."""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paathguide.data_loader import load_sample_data
from paathguide.fuzzy_search import SGGSFuzzySearcher
from paathguide.models import SessionLocal, create_tables


def test_fuzzy_search():
    """Test the fuzzy search functionality."""
    print("🔍 Testing SGGS Fuzzy Search...")
    
    # Create tables and load sample data
    create_tables()
    db = SessionLocal()
    
    try:
        # Load sample data
        load_sample_data(db)
        print("✅ Sample data loaded")
        
        # Initialize fuzzy searcher
        fuzzy_searcher = SGGSFuzzySearcher(db)
        
        # Test query (your example with STT errors)
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
