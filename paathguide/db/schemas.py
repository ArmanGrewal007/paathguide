"""Pydantic schemas for API request/response models."""

from datetime import datetime

from pydantic import BaseModel, Field


class SGGSTextBase(BaseModel):
    """Base schema for SGGS text data."""

    gurmukhi_text: str = Field(..., description="The Gurmukhi text of the verse")
    page_number: int | None = Field(None, description="Page number in SGGS")
    line_number: int | None = Field(None, description="Line number on the page")
    transliteration: str | None = Field(default=None, description="Roman transliteration")
    translation: str | None = Field(default=None, description="English translation")
    raag: str | None = Field(default=None, description="Musical raag")
    author: str | None = Field(default=None, description="Author (Guru/Bhagat)")


class SGGSTextCreate(SGGSTextBase):
    """Schema for creating new SGGS text."""

    pass


class SGGSTextUpdate(BaseModel):
    """Schema for updating SGGS text."""

    gurmukhi_text: str | None = None
    transliteration: str | None = None
    translation: str | None = None
    raag: str | None = None
    author: str | None = None


class SGGSText(SGGSTextBase):
    """Schema for SGGS text response."""

    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Backward compatibility aliases
VerseBase = SGGSTextBase
VerseCreate = SGGSTextCreate
VerseUpdate = SGGSTextUpdate
Verse = SGGSText


class VerseSearchQuery(BaseModel):
    """Schema for search queries."""

    query: str = Field(..., description="Search text")
    page_number: int | None = Field(default=None, description="Filter by page number")
    raag: str | None = Field(default=None, description="Filter by raag")
    author: str | None = Field(default=None, description="Filter by author")
    limit: int = Field(default=20, le=100, description="Maximum results to return")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")


class SearchResponse(BaseModel):
    """Schema for search response."""

    verses: list[SGGSText]  # Updated to use SGGSText instead of Verse
    total: int
    limit: int
    offset: int


class PageResponse(BaseModel):
    """Schema for page content response."""

    page_number: int
    verses: list[SGGSText]  # Updated to use SGGSText instead of Verse
    total_lines: int


class StatsResponse(BaseModel):
    """Schema for database statistics."""

    total_verses: int
    total_pages: int
    verses_with_translations: int
    verses_with_transliterations: int
    unique_raags: int
    unique_authors: int


class FuzzySearchRequest(BaseModel):
    """Schema for fuzzy search requests."""
    query_text: str = Field(..., description="Text to search for")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of results")
    score_cutoff: float = Field(default=60.0, ge=0.0, le=100.0, description="Minimum similarity score")
    ratio_type: str = Field(default="WRatio", description="Fuzzy matching algorithm")
    clean_text: bool = Field(default=True, description="Apply text preprocessing")


class FuzzySearchResult(BaseModel):
    """Schema for fuzzy search result."""
    verse: SGGSText  # Updated to use SGGSText instead of Verse
    score: float = Field(..., description="Similarity score (0-100)")
    ratio_type: str = Field(..., description="Fuzzy matching algorithm used")

    class Config:
        from_attributes = True


class FuzzySearchResponse(BaseModel):
    """Schema for fuzzy search response."""
    query_text: str
    results: list[FuzzySearchResult]
    total_found: int
    search_params: dict


class FuzzyComparisonResponse(BaseModel):
    """Schema for fuzzy comparison using multiple methods."""
    query_text: str
    methods: dict[str, list[FuzzySearchResult]]
    best_overall: FuzzySearchResult | None
