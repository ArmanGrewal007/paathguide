"""Text cleaning and preprocessing utilities for SGGS text."""

import logging
import re
import unicodedata


class WhisperTextCleaner:
    """Text cleaning and preprocessing for SGGS Gurmukhi text."""

    def __init__(self, enable_logging: bool = True):
        """Initialize the text cleaner with predefined mappings and patterns.
        
        Args:
            enable_logging: Whether to enable detailed step-by-step logging
        """
        self.enable_logging = enable_logging
        self.logger = logging.getLogger(__name__)

        if enable_logging and not self.logger.handlers:
            # Configure logging if not already configured
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        # Common STT error mappings for Gurmukhi
        self.character_mappings = {
            # Common misrecognitions
            "ਤ੍ਯ": "ਧਿ",
            "ਨਾਤ੍ਯਾਂ": "ਨਾ",
            "ਜਾਤ੍ਯ": "ਜਾ",
            "ਸਂਤਮ": "ਸੰਤ",
            "ਪਾਂ": "ਪਾ",
            "ਚਾਂ": "ਚਾ",
            "ਮਂ": "ਮ",
            "ਰਂ": "ਰ",
            # Add more mappings as you discover them
        }

        # Words that are commonly split or joined incorrectly
        self.word_mappings = {
            "ਸੇਖ ਮਾਰੇ": "ਸੇਵਕ",
            "ਤਾਰੀਆ ਚੁਂ": "ਤਾਰੀਐ",
            "ਸਾਤਰਾ ਮਾਰੇ": "ਸਤਿਗੁਰ",
            # Add more as needed
        }

        # Common repeated patterns to normalize
        self.repeated_patterns = [
            (r"(ਸ਼ਿ\s*){2,}", "ਸ਼ਿ"),
            (r"(ਚੁਂ\s*){2,}", "ਚੁਂ"),
        ]

    def _log_transformation(self, step: str, text: str) -> None:
        """Log text transformation step."""
        if self.enable_logging and text:
            self.logger.info(f"Step: {step:<33} Text: '{text}'")

    def clean_stt_output(self, text: str) -> str:
        """
        Clean speech-to-text output with comprehensive preprocessing steps.
        This is the main cleaning method that includes all available cleaning techniques:
        - Unicode normalization
        - Whitespace normalization 
        - Repeated character fixing
        - Character and word mappings
        - Pattern normalization
        - Aggressive cleaning (short word removal, punctuation cleanup)
        - Selective diacritic removal
        - Conjunct normalization
        - Content word extraction
        
        Args:
            text: Raw STT output text
            
        Returns:
            Fully cleaned and optimized text
        """
        if not text:
            return ""

        if self.enable_logging:
            self.logger.info("=" * 60)
            self.logger.info("STARTING TEXT CLEANING PROCESS")
            self.logger.info("=" * 60)

        current_text = text
        self._log_transformation("0. Original", current_text)

        # Step 1: Basic normalization
        current_text = self._normalize_unicode(current_text)
        self._log_transformation("1. Unicode Normalization", current_text)

        # Step 2: Remove extra whitespace
        current_text = self._normalize_whitespace(current_text)
        self._log_transformation("2. Whitespace Normalization", current_text)

        # Step 3: Fix repeated characters
        current_text = self._fix_repeated_characters(current_text)
        self._log_transformation("3. Fix Repeated Characters", current_text)

        # Step 4: Apply character mappings
        current_text = self._apply_character_mappings(current_text)
        self._log_transformation("4. Character Mappings", current_text)

        # Step 5: Apply word mappings
        current_text = self._apply_word_mappings(current_text)
        self._log_transformation("5. Word Mappings", current_text)

        # Step 6: Handle repeated patterns
        current_text = self._normalize_repeated_patterns(current_text)
        self._log_transformation("6. Normalize Repeated Patterns", current_text)

        # Step 7: Aggressive cleaning (always applied)
        current_text = self._aggressive_clean(current_text)
        self._log_transformation("7. Aggressive Cleaning", current_text)

        # Step 8: Additional cleaning methods for better matching
        current_text = self._remove_diacritics_selectively(current_text)
        self._log_transformation("8. Remove Diacritics Selectively", current_text)

        current_text = self._normalize_conjuncts(current_text)
        self._log_transformation("9. Normalize Conjuncts", current_text)

        current_text = self._extract_content_words(current_text)
        self._log_transformation("10. Extract Content Words", current_text)

        final_result = current_text.strip()
        self._log_transformation("11. Final Strip", final_result)

        if self.enable_logging:
            self.logger.info("=" * 60)
            self.logger.info("CLEANING PROCESS COMPLETED")
            self.logger.info("=" * 60)

        return final_result

    def _normalize_unicode(self, text: str) -> str:
        """Normalize Unicode characters."""
        # Normalize to NFD then back to NFC to handle different encodings
        text = unicodedata.normalize("NFD", text)
        text = unicodedata.normalize("NFC", text)
        return text

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace characters."""
        # Replace multiple whitespace with single space
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _fix_repeated_characters(self, text: str) -> str:
        """Fix repeated characters like ਪੱੱਾਦ -> ਪਾਦ."""
        # Remove excessive repetition of same character (3+ times)
        text = re.sub(r"(.)\1{2,}", r"\1", text)
        return text

    def _apply_character_mappings(self, text: str) -> str:
        """Apply predefined character mappings."""
        for wrong, correct in self.character_mappings.items():
            text = text.replace(wrong, correct)
        return text

    def _apply_word_mappings(self, text: str) -> str:
        """Apply predefined word mappings."""
        for wrong, correct in self.word_mappings.items():
            text = text.replace(wrong, correct)
        return text

    def _normalize_repeated_patterns(self, text: str) -> str:
        """Normalize repeated patterns using regex."""
        for pattern, replacement in self.repeated_patterns:
            text = re.sub(pattern, replacement, text)
        return text

    def _aggressive_clean(self, text: str) -> str:
        """Apply more aggressive cleaning."""
        # Remove very short words (likely artifacts)
        words = text.split()
        words = [word for word in words if len(word) > 1 or word in ["ਸ", "ਤ", "ਨ"]]  # Keep important single chars

        # Remove words with excessive punctuation
        words = [word for word in words if not re.match(r"^[^\w\s]{3,}$", word)]

        return " ".join(words)

    def _remove_diacritics_selectively(self, text: str) -> str:
        """Selectively remove some diacritics that cause matching issues."""
        # This is tricky for Gurmukhi - be very careful
        # Only remove certain marks that are commonly misrecognized
        text = re.sub(r"੍", "", text)  # Remove halant in some cases
        return text

    def _normalize_conjuncts(self, text: str) -> str:
        """Normalize conjunct consonants that might be split."""
        # Handle common conjuncts that get split by STT
        conjunct_mappings = {
            "ਸ ਤ": "ਸਤ",
            "ਗ ੁਰ": "ਗੁਰ",
            "ਪ ਰ": "ਪਰ",
        }

        for split, joined in conjunct_mappings.items():
            text = text.replace(split, joined)

        return text

    def _extract_content_words(self, text: str) -> str:
        """Extract main content words for better matching."""
        words = text.split()

        # Remove very common function words that don't help matching
        stop_words = {"ਹੈ", "ਹੋ", "ਨੈ", "ਤੇ", "ਦੇ", "ਨੂੰ"}  # Add more as needed
        content_words = [word for word in words if word not in stop_words]

        # If we removed too much, keep original
        if len(content_words) < len(words) * 0.3:  # Keep at least 30% of words
            return text

        return " ".join(content_words)

    def compare_cleaning_methods(self, text: str) -> dict[str, str]:
        """
        Compare different cleaning methods for analysis.
        
        Args:
            text: Input text to clean
            
        Returns:
            Dictionary with different cleaning results
        """
        return {
            "original": text,
            "cleaned": self.clean_stt_output(text),
        }

    def add_character_mapping(self, wrong: str, correct: str) -> None:
        """Add a new character mapping."""
        self.character_mappings[wrong] = correct

    def add_word_mapping(self, wrong: str, correct: str) -> None:
        """Add a new word mapping."""
        self.word_mappings[wrong] = correct

    def get_cleaning_stats(self, original: str, cleaned: str) -> dict[str, int | float]:
        """
        Get statistics about the cleaning process.
        
        Args:
            original: Original text
            cleaned: Cleaned text
            
        Returns:
            Dictionary with cleaning statistics
        """
        return {
            "original_length": len(original),
            "cleaned_length": len(cleaned),
            "original_words": len(original.split()),
            "cleaned_words": len(cleaned.split()),
            "reduction_percent": round((len(original) - len(cleaned)) / len(original) * 100, 2) if original else 0
        }


def main():
    """Test the WhisperTextCleaner with sample STT output."""
    # Test string with STT errors
    stt_text = "ਗੁਰ ਪੱੱਾਦ ਜਾਪ ਆਦ ਸਾਚ ਜਗਾਦ ਸਾਚ ਹਿ ਸਾਚ ਨਾਨਕ ਹੋ ਸੀਬੀ ਸਾਚ ਸਚ਼ਿ ਸ਼ਿ ਸ਼ਿ ਸ਼ਿ ਸ਼ਿ"

    print("=" * 80)
    print("WHISPER TEXT CLEANER TESTS")
    print("=" * 80)
    print(f"Original STT: '{stt_text}'")
    print(f"Length: {len(stt_text)} characters, {len(stt_text.split())} words")
    print()

    # Create cleaner with logging enabled
    cleaner = WhisperTextCleaner(enable_logging=True)

    # print("🔍 TESTING BASIC CLEANING:")
    # print("-" * 40)
    # basic_result = cleaner.clean_stt_output(stt_text, aggressive=False)
    # print(f"Result: '{basic_result}'")
    # print()

    # print("🔥 TESTING AGGRESSIVE CLEANING:")
    # print("-" * 40)
    # aggressive_result = cleaner.clean_stt_output(stt_text, aggressive=True)
    # print(f"Result: '{aggressive_result}'")
    # print()

    matching_result = cleaner.clean_stt_output(stt_text)
    print(f"Result: '{matching_result}'")
    print()

    # print("📊 COMPARISON OF ALL METHODS:")
    # print("-" * 40)
    # comparison = cleaner.compare_cleaning_methods(stt_text)
    # for method, result in comparison.items():
    #     print(f"{method:12}: '{result}'")
    # print()

    # print("📈 CLEANING STATISTICS:")
    # print("-" * 40)
    # for method, result in comparison.items():
    #     if method != 'original':
    #         stats = cleaner.get_cleaning_stats(stt_text, result)
    #         print(f"{method:12}: {stats['original_words']} → {stats['cleaned_words']} words, "
    #               f"{stats['reduction_percent']}% reduction")
    # print()


if __name__ == "__main__":
    main()
