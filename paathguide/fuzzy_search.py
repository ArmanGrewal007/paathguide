"""Fuzzy search functionality for SGGS verses."""

from typing import Any

from rapidfuzz import fuzz, process
from sqlalchemy.orm import Session

from paathguide.db import models
from paathguide.db.repository import VerseRepository
from paathguide.text_cleaner import WhisperTextCleaner


class FuzzySearchResult:
    """Result of a fuzzy search operation."""

    def __init__(self, verse: models.Verse, score: float, ratio_type: str):
        self.verse = verse
        self.score = score
        self.ratio_type = ratio_type


class SGGSFuzzySearcher:
    """Fuzzy search functionality for SGGS verses."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = VerseRepository(db)
        self.text_cleaner = WhisperTextCleaner()

    def _get_all_verses_text(self) -> dict[str, models.Verse]:
        """Get all verses as a dictionary mapping text to verse objects."""
        verses = self.db.query(models.Verse).all()
        return {str(verse.gurmukhi_text): verse for verse in verses}

    def find_closest_matches(
        self,
        query_text: str,
        limit: int = 10,
        score_cutoff: float = 60.0,
        ratio_type: str = "WRatio",
    ) -> list[FuzzySearchResult]:
        """
        Find the closest matching verses using fuzzy string matching.

        Args:
            query_text: The text to search for
            limit: Maximum number of results to return
            score_cutoff: Minimum similarity score (0-100)
            ratio_type: Type of ratio calculation ('ratio', 'partial_ratio', 'token_sort_ratio', 'WRatio')

        Returns:
            List of FuzzySearchResult objects sorted by similarity score (highest first)
        """
        verses_dict = self._get_all_verses_text()

        if not verses_dict:
            return []

        # Choose the appropriate fuzzy matching function
        ratio_func = self._get_ratio_function(ratio_type)

        # Use rapidfuzz's process.extract for efficient batch processing
        matches = process.extract(
            query_text,
            verses_dict.keys(),
            scorer=ratio_func,
            limit=limit,
            score_cutoff=score_cutoff,
        )

        # Convert to FuzzySearchResult objects
        results = []
        for text, score, _ in matches:
            verse = verses_dict[text]
            result = FuzzySearchResult(verse=verse, score=score, ratio_type=ratio_type)
            results.append(result)

        return results

    def find_best_match(self, query_text: str, score_cutoff: float = 60.0, ratio_type: str = "WRatio") -> FuzzySearchResult | None:
        """
        Find the single best matching verse.

        Args:
            query_text: The text to search for
            score_cutoff: Minimum similarity score (0-100)
            ratio_type: Type of ratio calculation

        Returns:
            FuzzySearchResult object or None if no match above cutoff
        """
        results = self.find_closest_matches(
            query_text, limit=1, score_cutoff=score_cutoff, ratio_type=ratio_type
        )
        return results[0] if results else None

    def compare_with_multiple_methods(
        self, query_text: str, limit: int = 5, score_cutoff: float = 50.0
    ) -> dict[str, list[FuzzySearchResult]]:
        """
        Compare the query text using multiple fuzzy matching methods.

        Args:
            query_text: The text to search for
            limit: Maximum number of results per method
            score_cutoff: Minimum similarity score

        Returns:
            Dictionary with method names as keys and results as values
        """
        methods = ["ratio", "partial_ratio", "token_sort_ratio", "WRatio"]
        results = {}

        for method in methods:
            results[method] = self.find_closest_matches(
                query_text, limit=limit, score_cutoff=score_cutoff, ratio_type=method
            )

        return results

    def _get_ratio_function(self, ratio_type: str) -> Any:
        """Get the appropriate ratio function from rapidfuzz."""
        ratio_functions = {
            "ratio": fuzz.ratio,
            "partial_ratio": fuzz.partial_ratio,
            "token_sort_ratio": fuzz.token_sort_ratio,
            "token_set_ratio": fuzz.token_set_ratio,
            "WRatio": fuzz.WRatio,  # Weighted ratio (recommended for most cases)
        }

        return ratio_functions.get(ratio_type, fuzz.WRatio)

    def search_with_preprocessing(
        self,
        query_text: str,
        limit: int = 10,
        score_cutoff: float = 60.0,
        clean_text: bool = True,
    ) -> list[FuzzySearchResult]:
        """
        Search with optional text preprocessing.

        Args:
            query_text: The text to search for
            limit: Maximum number of results
            score_cutoff: Minimum similarity score
            clean_text: Whether to apply text cleaning

        Returns:
            List of FuzzySearchResult objects
        """
        processed_query = query_text
        if clean_text:
            processed_query = self.text_cleaner.clean_stt_output(query_text)

        return self.find_closest_matches(
            processed_query, limit=limit, score_cutoff=score_cutoff
        )

    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for better matching.
        This could include removing extra spaces, normalizing characters, etc.
        """
        import re

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Remove repeated characters (like in your example: ਪੱੱਾਦ -> ਪਾਦ)
        text = re.sub(r"(.)\1{2,}", r"\1", text)

        # Remove repeated patterns like ਸ਼ਿ ਸ਼ਿ ਸ਼ਿ -> ਸ਼ਿ
        text = re.sub(r"(ਸ਼ਿ\s*){2,}", "ਸ਼ਿ", text)

        return text.strip()

    def get_similarity_score(self, text1: str, text2: str, ratio_type: str = "WRatio") -> float:
        """
        Get similarity score between two texts.

        Args:
            text1: First text
            text2: Second text
            ratio_type: Type of ratio calculation

        Returns:
            Similarity score (0-100)
        """
        ratio_func = self._get_ratio_function(ratio_type)
        return ratio_func(text1, text2)

    def compare_cleaning_approaches(
        self, query_text: str, limit: int = 3, score_cutoff: float = 30.0
    ) -> dict[str, dict[str, str | list[FuzzySearchResult]]]:
        """
        Compare fuzzy search results using different cleaning approaches.
        
        Args:
            query_text: The text to search for
            limit: Maximum number of results per approach
            score_cutoff: Minimum similarity score
            
        Returns:
            Dictionary with cleaning approach names as keys and results as values
        """
        approaches = {
            "no_cleaning": query_text,
            "cleaning": self.text_cleaner.clean_stt_output(query_text),
        }

        results = {}
        for approach, cleaned_query in approaches.items():
            results[approach] = {
                "cleaned_query": cleaned_query,
                "results": self.find_closest_matches(
                    cleaned_query, limit=limit, score_cutoff=score_cutoff
                )
            }

        return results
