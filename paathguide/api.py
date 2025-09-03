"""FastAPI application for SGGS API."""

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn

from paathguide.data_loader import SGGSDataLoader, load_sample_data
from paathguide.db import schemas
from paathguide.db.models import create_tables, get_db
from paathguide.fuzzy_search import SGGSFuzzySearcher
from paathguide.db.repository import VerseRepository

# Create FastAPI app
app = FastAPI(
    title="SGGS API",
    description="API for Shri Guru Granth Sahib verses and search",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Create tables on startup
@app.on_event("startup")
def startup_event():
    create_tables()
    print("Database tables created")


# Health check
@app.get("/", summary="Health Check")
def read_root():
    return {"message": "SGGS API is running", "status": "healthy"}


# Verse CRUD endpoints
@app.post("/verses/", response_model=schemas.Verse, summary="Create a new verse")
def create_verse(verse: schemas.VerseCreate, db: Session = Depends(get_db)):
    """Create a new verse."""
    repo = VerseRepository(db)
    return repo.create_verse(verse)


@app.get("/verses/{verse_id}", response_model=schemas.Verse, summary="Get verse by ID")
def get_verse(verse_id: int, db: Session = Depends(get_db)):
    """Get a specific verse by ID."""
    repo = VerseRepository(db)
    verse = repo.get_verse(verse_id)
    if not verse:
        raise HTTPException(status_code=404, detail="Verse not found")
    return verse


@app.get("/verses/", response_model=list[schemas.Verse], summary="List verses")
def list_verses(
    skip: int = Query(0, ge=0, description="Number of verses to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of verses to return"),
    db: Session = Depends(get_db),
):
    """List verses with pagination."""
    repo = VerseRepository(db)
    return repo.get_verses(skip=skip, limit=limit)


@app.put("/verses/{verse_id}", response_model=schemas.Verse, summary="Update verse")
def update_verse(verse_id: int, verse_update: schemas.VerseUpdate, db: Session = Depends(get_db)):
    """Update a verse."""
    repo = VerseRepository(db)
    updated_verse = repo.update_verse(verse_id, verse_update)
    if not updated_verse:
        raise HTTPException(status_code=404, detail="Verse not found")
    return updated_verse


@app.delete("/verses/{verse_id}", summary="Delete verse")
def delete_verse(verse_id: int, db: Session = Depends(get_db)):
    """Delete a verse."""
    repo = VerseRepository(db)
    if not repo.delete_verse(verse_id):
        raise HTTPException(status_code=404, detail="Verse not found")
    return {"message": "Verse deleted successfully"}


# Search and navigation endpoints
@app.post("/search/", response_model=schemas.SearchResponse, summary="Search verses")
def search_verses(query: schemas.VerseSearchQuery, db: Session = Depends(get_db)):
    """Search verses based on text and filters."""
    repo = VerseRepository(db)
    verses, total = repo.search_verses(query)

    return {
        "verses": verses,
        "total": total,
        "limit": query.limit,
        "offset": query.offset,
    }


@app.get("/search/", response_model=schemas.SearchResponse, summary="Search verses (GET)")
def search_verses_get(
    q: str = Query(..., description="Search query"),
    page_number: int | None = Query(None, description="Filter by page number"),
    raag: str | None = Query(None, description="Filter by raag"),
    author: str | None = Query(None, description="Filter by author"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
):
    """Search verses using GET parameters."""
    query = schemas.VerseSearchQuery(
        query=q,
        page_number=page_number,
        raag=raag,
        author=author,
        limit=limit,
        offset=offset,
    )
    return search_verses(query, db)


@app.get("/pages/{page_number}", response_model=schemas.PageResponse, summary="Get page content")
def get_page(page_number: int, db: Session = Depends(get_db)):
    """Get all verses from a specific page."""
    repo = VerseRepository(db)
    verses = repo.get_page_content(page_number)

    return {"page_number": page_number, "verses": verses, "total_lines": len(verses)}


@app.get("/verses/{verse_id}/context", response_model=list[schemas.Verse], summary="Get verse context")
def get_verse_context(
    verse_id: int,
    context: int = Query(3, ge=1, le=10, description="Number of lines before/after"),
    db: Session = Depends(get_db),
):
    """Get verses around a specific verse for context."""
    repo = VerseRepository(db)
    context_verses = repo.get_surrounding_verses(verse_id, context)
    if not context_verses:
        raise HTTPException(status_code=404, detail="Verse not found")
    return context_verses


@app.get("/verses/page/{page}/line/{line}", response_model=schemas.Verse, summary="Get verse by page and line")
def get_verse_by_location(page: int, line: int, db: Session = Depends(get_db)):
    """Get verse by page and line number."""
    repo = VerseRepository(db)
    verse = repo.get_verse_by_page_line(page, line)
    if not verse:
        raise HTTPException(status_code=404, detail="Verse not found at specified location")
    return verse


@app.get("/random", response_model=schemas.Verse, summary="Get random verse")
def get_random_verse(db: Session = Depends(get_db)):
    """Get a random verse (Hukamnama style)."""
    repo = VerseRepository(db)
    verse = repo.get_random_verse()
    if not verse:
        raise HTTPException(status_code=404, detail="No verses found")
    return verse


# Fuzzy search endpoints
@app.post("/fuzzy-search/", response_model=schemas.FuzzySearchResponse, summary="Fuzzy search verses")
def fuzzy_search_verses(
    search_request: schemas.FuzzySearchRequest,
    db: Session = Depends(get_db)
):
    """Find verses using fuzzy string matching."""
    fuzzy_searcher = SGGSFuzzySearcher(db)

    results = fuzzy_searcher.search_with_preprocessing(
        query_text=search_request.query_text,
        limit=search_request.limit,
        score_cutoff=search_request.score_cutoff
    )

    # Convert to response format
    fuzzy_results = [
        schemas.FuzzySearchResult(
            verse=result.verse,
            score=result.score,
            ratio_type=result.ratio_type
        )
        for result in results
    ]

    return schemas.FuzzySearchResponse(
        query_text=search_request.query_text,
        results=fuzzy_results,
        total_found=len(fuzzy_results),
        search_params=search_request.model_dump()
    )


@app.get("/fuzzy-search/", response_model=schemas.FuzzySearchResponse, summary="Fuzzy search verses (GET)")
def fuzzy_search_verses_get(
    query_text: str = Query(..., description="Text to search for"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    score_cutoff: float = Query(60.0, ge=0.0, le=100.0, description="Minimum similarity score"),
    ratio_type: str = Query("WRatio", description="Fuzzy matching algorithm"),
    clean_text: bool = Query(True, description="Apply text preprocessing"),
    db: Session = Depends(get_db)
):
    """Find verses using fuzzy string matching (GET endpoint)."""
    search_request = schemas.FuzzySearchRequest(
        query_text=query_text,
        limit=limit,
        score_cutoff=score_cutoff,
        ratio_type=ratio_type,
        clean_text=clean_text
    )
    return fuzzy_search_verses(search_request, db)


@app.post("/fuzzy-search/compare", response_model=schemas.FuzzyComparisonResponse, summary="Compare fuzzy search methods")
def compare_fuzzy_methods(
    query_text: str = Query(..., description="Text to search for"),
    limit: int = Query(5, ge=1, le=20, description="Results per method"),
    score_cutoff: float = Query(50.0, ge=0.0, le=100.0, description="Minimum similarity score"),
    db: Session = Depends(get_db)
):
    """Compare the query using multiple fuzzy matching methods."""
    fuzzy_searcher = SGGSFuzzySearcher(db)

    methods_results = fuzzy_searcher.compare_with_multiple_methods(
        query_text=query_text,
        limit=limit,
        score_cutoff=score_cutoff
    )

    # Convert to response format
    response_methods = {}
    best_result = None
    best_score = 0.0

    for method, results in methods_results.items():
        method_results = [
            schemas.FuzzySearchResult(
                verse=result.verse,
                score=result.score,
                ratio_type=result.ratio_type
            )
            for result in results
        ]
        response_methods[method] = method_results

        # Track the best result across all methods
        if method_results and method_results[0].score > best_score:
            best_score = method_results[0].score
            best_result = method_results[0]

    return schemas.FuzzyComparisonResponse(
        query_text=query_text,
        methods=response_methods,
        best_overall=best_result
    )


@app.get("/fuzzy-search/best-match", response_model=schemas.FuzzySearchResult | None, summary="Find best match")
def find_best_match(
    query_text: str = Query(..., description="Text to search for"),
    score_cutoff: float = Query(60.0, ge=0.0, le=100.0, description="Minimum similarity score"),
    ratio_type: str = Query("WRatio", description="Fuzzy matching algorithm"),
    db: Session = Depends(get_db)
):
    """Find the single best matching verse."""
    fuzzy_searcher = SGGSFuzzySearcher(db)

    result = fuzzy_searcher.find_best_match(
        query_text=query_text,
        score_cutoff=score_cutoff,
        ratio_type=ratio_type
    )

    if result:
        return schemas.FuzzySearchResult(
            verse=result.verse,
            score=result.score,
            ratio_type=result.ratio_type
        )
    return None


# Statistics endpoint
@app.get("/stats", response_model=schemas.StatsResponse, summary="Get database statistics")
def get_stats(db: Session = Depends(get_db)):
    """Get database statistics and metrics."""
    repo = VerseRepository(db)
    return repo.get_stats()


# Data management endpoints
@app.post("/admin/load-data", summary="Load data from DOCX file")
def load_data_from_docx(
    file_path: str = Query(..., description="Path to DOCX file"),
    skip_first: int = Query(2, description="Number of initial lines to skip"),
    clear_existing: bool = Query(False, description="Clear existing data first"),
    db: Session = Depends(get_db),
):
    """Load SGGS data from DOCX file."""
    try:
        loader = SGGSDataLoader(db)

        if clear_existing:
            loader.clear_database()

        count = loader.load_from_docx_line_by_line(file_path, skip_first)
        return {"message": f"Successfully loaded {count} verses", "count": count}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}") from e


@app.post("/admin/load-sample", summary="Load sample data")
def load_sample_data_endpoint(db: Session = Depends(get_db)):
    """Load sample verses for testing."""
    try:
        load_sample_data(db)
        return {"message": "Sample data loaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading sample data: {str(e)}") from e


@app.delete("/admin/clear-data", summary="Clear all data")
def clear_all_data(db: Session = Depends(get_db)):
    """Clear all verses from the database."""
    try:
        loader = SGGSDataLoader(db)
        loader.clear_database()
        return {"message": "Database cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing data: {str(e)}") from e


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
