"""Fuzzy search implementation for matching whisper output to SGGS text."""

import re
from sqlalchemy.orm import Session
from typing import List, Tuple, Optional
from dataclasses import dataclass
from difflib import SequenceMatcher

from paathguide.cleaner.text_cleaner import WhisperTextCleaner
from paathguide.db.repository import SGGSTextRepository
from paathguide.db.models import SGGSText, SessionLocal
from paathguide.db.schemas import VerseSearchQuery


@dataclass
class FuzzyMatch:
    """Represents a fuzzy match result with similarity score."""
    text: SGGSText
    similarity_score: float
    match_type: str  # 'exact', 'ngram', 'phonetic', 'edit_distance'
    matched_portion: str


class GurmukliPhoneticMapper:
    """Maps similar sounding Gurmukhi characters for phonetic matching."""
    
    # Phonetically similar character groups
    PHONETIC_GROUPS = {
        # Vowel variations
        'ਿ': ['ਿ', 'ੇ', 'ੈ'],  # i, e, ai sounds
        'ੇ': ['ਿ', 'ੇ', 'ੈ'],
        'ੈ': ['ਿ', 'ੇ', 'ੈ'],
        
        # Consonant variations  
        'ਕ': ['ਕ', 'ਗ'],  # k, g
        'ਗ': ['ਕ', 'ਗ'],
        'ਤ': ['ਤ', 'ਦ'],  # t, d
        'ਦ': ['ਤ', 'ਦ'],
        'ਪ': ['ਪ', 'ਬ'],  # p, b
        'ਬ': ['ਪ', 'ਬ'],
        
        # Aspirated vs non-aspirated
        'ਚ': ['ਚ', 'ਛ'],  # ch, chh
        'ਛ': ['ਚ', 'ਛ'],
        'ਟ': ['ਟ', 'ਠ'],  # t, th
        'ਠ': ['ਟ', 'ਠ'],
        
        # Similar sounds
        'ਸ': ['ਸ', 'ਸ਼'],  # s, sh
        'ਸ਼': ['ਸ', 'ਸ਼'],
    }
    
    @classmethod
    def get_phonetic_variants(cls, char: str) -> List[str]:
        """Get phonetically similar characters for a given character."""
        return cls.PHONETIC_GROUPS.get(char, [char])
    
    @classmethod
    def are_phonetically_similar(cls, char1: str, char2: str) -> bool:
        """Check if two characters are phonetically similar."""
        variants1 = set(cls.get_phonetic_variants(char1))
        variants2 = set(cls.get_phonetic_variants(char2))
        return bool(variants1 & variants2)


class NGramMatcher:
    """N-gram based text matching for handling character substitutions."""
    
    @staticmethod
    def get_character_ngrams(text: str, n: int = 3) -> set:
        """Extract character n-grams from text."""
        # Remove spaces and punctuation for better matching
        clean_text = re.sub(r'[^\u0A00-\u0A7F]', '', text)  # Keep only Gurmukhi
        if len(clean_text) < n:
            return {clean_text}
        
        ngrams = set()
        for i in range(len(clean_text) - n + 1):
            ngrams.add(clean_text[i:i+n])
        return ngrams
    
    @staticmethod
    def calculate_ngram_similarity(text1: str, text2: str, n: int = 3) -> float:
        """Calculate similarity between two texts using n-gram overlap."""
        ngrams1 = NGramMatcher.get_character_ngrams(text1, n)
        ngrams2 = NGramMatcher.get_character_ngrams(text2, n)
        
        if not ngrams1 and not ngrams2:
            return 1.0
        if not ngrams1 or not ngrams2:
            return 0.0
        
        intersection = len(ngrams1 & ngrams2)
        union = len(ngrams1 | ngrams2)
        
        return intersection / union if union > 0 else 0.0


class WeightedEditDistance:
    """Edit distance with custom weights for Gurmukhi characters."""
    
    @staticmethod
    def calculate_weighted_distance(s1: str, s2: str) -> float:
        """Calculate weighted edit distance between two strings."""
        len1, len2 = len(s1), len(s2)
        
        # Create DP table with float values
        dp = [[0.0] * (len2 + 1) for _ in range(len1 + 1)]
        
        # Initialize base cases
        for i in range(len1 + 1):
            dp[i][0] = float(i)
        for j in range(len2 + 1):
            dp[0][j] = float(j)
        
        # Fill DP table
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if s1[i-1] == s2[j-1]:
                    dp[i][j] = dp[i-1][j-1]  # No cost for exact match
                else:
                    # Check if phonetically similar (lower cost)
                    if GurmukliPhoneticMapper.are_phonetically_similar(s1[i-1], s2[j-1]):
                        substitution_cost = 0.5  # Lower cost for phonetic similarity
                    else:
                        substitution_cost = 1.0  # Normal cost
                    
                    dp[i][j] = min(
                        dp[i-1][j] + 1.0,      # Deletion
                        dp[i][j-1] + 1.0,      # Insertion
                        dp[i-1][j-1] + substitution_cost  # Substitution
                    )
        
        # Normalize by max length
        max_len = max(len1, len2)
        return 1.0 - (dp[len1][len2] / max_len) if max_len > 0 else 1.0


class WordLevelMatcher:
    """Handle word-level variations like splitting and merging."""
    
    @staticmethod
    def create_word_variants(text: str) -> List[str]:
        """Create variants by splitting and merging words."""
        words = text.split()
        variants = [text]  # Original text
        
        # Word splitting variants (split each word into characters with spaces)
        if words:
            split_variant = ' '.join(' '.join(word) for word in words)
            variants.append(split_variant)
            
            # Word merging variant (no spaces)
            merged_variant = ''.join(words)
            variants.append(merged_variant)
            
            # Partial merging (merge adjacent words)
            if len(words) > 1:
                for i in range(len(words) - 1):
                    partial_merged = words.copy()
                    partial_merged[i] = partial_merged[i] + partial_merged[i + 1]
                    del partial_merged[i + 1]
                    variants.append(' '.join(partial_merged))
        
        return variants


class FuzzySearch:
    """Enhanced search SGGS using fuzzy matching for whisper output."""
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize with database session and text cleaner.
        
        Args:
            db: Optional database session. If None, creates a new one.
        """
        self.db = db or SessionLocal()
        self.cleaner = WhisperTextCleaner(enable_logging=False)
        self.repo = SGGSTextRepository(self.db)
        self._should_close_db = db is None
    
    def search(self, query_text: str, limit: int = 10, use_fuzzy: bool = True, 
              min_similarity: float = 0.3) -> Tuple[List[SGGSText], int]:
        """Search SGGS using whisper output with fuzzy matching.
        
        Args:
            query_text: Raw whisper transcription output
            limit: Maximum number of results to return
            use_fuzzy: Whether to use fuzzy matching if exact search fails
            min_similarity: Minimum similarity threshold for fuzzy matches
            
        Returns:
            Tuple of (search_results, total_count)
        """
        if not query_text.strip():
            return [], 0
        
        # Clean the whisper output
        cleaned_query = self.cleaner.clean_stt_output(query_text)
        
        if not cleaned_query.strip():
            return [], 0
        
        # First try exact FTS5 search
        if not use_fuzzy:
            search_query = VerseSearchQuery(query=cleaned_query, limit=limit, offset=0)
            results, total = self.repo.search_sggs_texts(search_query)
            
            if results or not use_fuzzy:
                print("✅Exact search succeeded.")
                return results, total

        # If exact search fails and fuzzy is enabled, try fuzzy search
        else:
            fuzzy_matches, fuzzy_total = self.fuzzy_search(query_text, cleaned_query, limit, min_similarity)
            # Convert FuzzyMatch objects back to SGGSText for compatibility
            results = [match.text for match in fuzzy_matches]
            return results, fuzzy_total
        
        return [], 0
    
    def fuzzy_search(self, original_query: str, cleaned_query: str, limit: int = 10, min_similarity: float = 0.3) -> Tuple[List[FuzzyMatch], int]:
        """Perform fuzzy search when exact search fails.
        
        Args:
            original_query: Raw whisper output
            cleaned_query: Cleaned whisper output
            limit: Maximum results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            Tuple of (fuzzy_matches, total_count)
        """
        fuzzy_matches = []
        
        # Get candidates for fuzzy matching (limit for performance)
        candidates = self.db.query(SGGSText).limit(500).all()
        
        # Create word variants for better matching
        query_variants = WordLevelMatcher.create_word_variants(cleaned_query)
        
        for text in candidates:
            best_score = 0.0
            best_type = ""
            best_portion = ""
            
            # Convert SQLAlchemy object to string
            text_content = str(text.gurmukhi_text) if hasattr(text, 'gurmukhi_text') and text.gurmukhi_text is not None else ""
            
            # Try different matching strategies
            for variant in query_variants:
                # Strategy 1: N-gram similarity
                ngram_score = NGramMatcher.calculate_ngram_similarity(variant, text_content, n=3)
                if ngram_score > best_score:
                    best_score = ngram_score
                    best_type = "ngram"
                    best_portion = variant
                
                # Strategy 2: Weighted edit distance (only for shorter texts)
                if len(variant) < 100 and len(text_content) < 200:
                    edit_score = WeightedEditDistance.calculate_weighted_distance(variant, text_content)
                    if edit_score > best_score:
                        best_score = edit_score
                        best_type = "edit_distance"
                        best_portion = variant
                
                # Strategy 3: Word-level partial matching
                words_in_text = text_content.split()
                variant_words = variant.split()
                
                for word in variant_words:
                    if len(word) > 2:  # Skip very short words
                        for text_word in words_in_text:
                            word_similarity = NGramMatcher.calculate_ngram_similarity(word, text_word, n=2)
                            if word_similarity > 0.7 and word_similarity > best_score:
                                best_score = word_similarity
                                best_type = "word_partial"
                                best_portion = f"{word} → {text_word}"
            
            # Add to results if above threshold
            if best_score >= min_similarity:
                fuzzy_matches.append(FuzzyMatch(text=text, similarity_score=best_score, 
                                                match_type=best_type, matched_portion=best_portion))

        # Sort by similarity score (descending)
        fuzzy_matches.sort(key=lambda x: x.similarity_score, reverse=True)
        
        # Return top results
        return fuzzy_matches[:limit], len(fuzzy_matches)
    
    def search_with_details(self, query_text: str, limit: int = 10, min_similarity: float = 0.3) -> Tuple[List[FuzzyMatch], int]:
        """Search with detailed fuzzy match information.
        
        Args:
            query_text: Raw whisper transcription output
            limit: Maximum number of results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            Tuple of (fuzzy_matches_with_details, total_count)
        """
        if not query_text.strip():
            return [], 0
        
        cleaned_query = self.cleaner.clean_stt_output(query_text)
        
        # Try exact search first
        try:
            search_query = VerseSearchQuery(query=cleaned_query, limit=limit, offset=0)
            results, total = self.repo.search_sggs_texts(search_query)
            
            if results:
                # Convert exact results to FuzzyMatch format
                exact_matches = [FuzzyMatch(text=result, similarity_score=1.0, 
                                            match_type='exact', matched_portion=cleaned_query) 
                                  for result in results]
                return exact_matches, total
                
        except Exception:
            pass
        
        # Fall back to fuzzy search
        return self.fuzzy_search(query_text, cleaned_query, limit, min_similarity)
    
    def get_cleaned_query(self, query_text: str) -> str:
        """Get the cleaned version of whisper output for debugging.
        
        Args:
            query_text: Raw whisper transcription output
            
        Returns:
            Cleaned query text
        """
        return self.cleaner.clean_stt_output(query_text)
    
    def close(self):
        """Close database connection if we created it."""
        if self._should_close_db and self.db:
            self.db.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
