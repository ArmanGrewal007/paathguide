"""FastAPI application for SGGS API with FTS5 support."""

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn

from paathguide.db.data_loader import SGGSDataLoader
from paathguide.db import schemas
from paathguide.db.models import create_tables, get_db
from paathguide.db.repository import SGGSTextRepository
from paathguide.search.fuzzy_search import FuzzySearch

# Create FastAPI app
app = FastAPI(
    title="SGGS API with FTS5",
    description="API for Shri Guru Granth Sahib verses and full-text search",
    version="2.0.0",
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
    return {"message": "SGGS API with FTS5 is running", "status": "healthy", "version": "2.0.0"}


# SGGS Text CRUD endpoints
@app.post("/verses/", response_model=schemas.SGGSText, summary="Create a new verse")
def create_verse(verse: schemas.SGGSTextCreate, db: Session = Depends(get_db)):
    """Create a new verse."""
    repo = SGGSTextRepository(db)
    return repo.create_sggs_text(verse)


@app.get("/verses/{verse_id}", response_model=schemas.SGGSText, summary="Get verse by ID")
def get_verse(verse_id: int, db: Session = Depends(get_db)):
    """Get a specific verse by ID."""
    repo = SGGSTextRepository(db)
    verse = repo.get_sggs_text(verse_id)
    if not verse:
        raise HTTPException(status_code=404, detail="Verse not found")
    return verse


@app.get("/verses/", response_model=list[schemas.SGGSText], summary="List verses")
def list_verses(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """List verses with pagination."""
    repo = SGGSTextRepository(db)
    return repo.get_sggs_texts(skip=skip, limit=limit)


@app.put("/verses/{verse_id}", response_model=schemas.SGGSText, summary="Update verse")
def update_verse(verse_id: int, verse_update: schemas.SGGSTextUpdate, db: Session = Depends(get_db)):
    """Update a verse."""
    repo = SGGSTextRepository(db)
    updated_verse = repo.update_sggs_text(verse_id, verse_update)
    if not updated_verse:
        raise HTTPException(status_code=404, detail="Verse not found")
    return updated_verse


@app.delete("/verses/{verse_id}", summary="Delete verse")
def delete_verse(verse_id: int, db: Session = Depends(get_db)):
    """Delete a verse."""
    repo = SGGSTextRepository(db)
    if not repo.delete_sggs_text(verse_id):
        raise HTTPException(status_code=404, detail="Verse not found")
    return {"message": "Verse deleted successfully"}


# Search endpoints with FTS5
@app.post("/search/", response_model=schemas.SearchResponse, summary="Search verses with FTS5")
def search_verses(search_query: schemas.VerseSearchQuery, db: Session = Depends(get_db)):
    """Search verses using FTS5 full-text search and filters."""
    repo = SGGSTextRepository(db)
    verses, total = repo.search_sggs_texts(search_query)
    # Convert ORM objects to Pydantic schema objects
    verses_schema = [schemas.SGGSText.from_orm(v) for v in verses]

    return schemas.SearchResponse(verses=verses_schema, total=total, 
                                  limit=search_query.limit, offset=search_query.offset)



@app.get("/search/", response_model=schemas.SearchResponse, summary="Search verses (GET method)")
def search_verses_get(
    query: str = Query(..., description="Search text"),
    page_number: int | None = Query(None, description="Filter by page number"),
    raag: str | None = Query(None, description="Filter by raag"),
    author: str | None = Query(None, description="Filter by author"),
    limit: int = Query(20, le=100, description="Maximum results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
):
    """Search verses using GET method with query parameters."""
    search_query = schemas.VerseSearchQuery(query=query, page_number=page_number, raag=raag,
                                            author=author, limit=limit, offset=offset)
    return search_verses(search_query, db)



@app.post("/fuzzy-search/", response_model=schemas.SearchResponse, summary="Fuzzy search using whisper output")
def fuzzy_search(
    query: str = Query(..., description="Raw whisper transcription or search query"),
    limit: int = Query(10, le=50, description="Maximum results to return"),
    use_fuzzy: bool = Query(True, description="Enable fuzzy matching"),
    min_similarity: float = Query(0.3, ge=0.0, le=1.0, description="Minimum similarity threshold"),
    db: Session = Depends(get_db),
):
    """Search SGGS using fuzzy matching for whisper output or imperfect queries."""
    searcher = FuzzySearch(db)
    try:
        verses, total = searcher.search(query, limit, use_fuzzy, min_similarity)
        # Convert ORM objects to Pydantic schema objects
        verses_schema = [schemas.SGGSText.from_orm(v) for v in verses]
        return schemas.SearchResponse(verses=verses_schema, total=total, limit=limit, offset=0)
    finally:
        # Don't close db here since it's managed by FastAPI
        pass


# Page and navigation endpoints
@app.get("/pages/{page_number}", response_model=schemas.PageResponse, summary="Get page content")
def get_page(page_number: int, db: Session = Depends(get_db)):
    """Get all verses from a specific page."""
    repo = SGGSTextRepository(db)
    verses = repo.get_page_content(page_number)

    return {"page_number": page_number, "verses": verses, "total_lines": len(verses)}


@app.get("/verses/{verse_id}/context", response_model=list[schemas.SGGSText], summary="Get verse context")
def get_verse_context(
    verse_id: int,
    context: int = Query(3, ge=1, le=10, description="Number of lines before/after"),
    db: Session = Depends(get_db),
):
    """Get verses around a specific verse for context."""
    repo = SGGSTextRepository(db)
    context_verses = repo.get_surrounding_texts(verse_id, context)
    if not context_verses:
        raise HTTPException(status_code=404, detail="Verse not found")
    return context_verses


@app.get("/verses/page/{page}/line/{line}", response_model=schemas.SGGSText, summary="Get verse by page and line")
def get_verse_by_location(page: int, line: int, db: Session = Depends(get_db)):
    """Get verse by page and line number."""
    repo = SGGSTextRepository(db)
    verse = repo.get_sggs_text_by_page_line(page, line)
    if not verse:
        raise HTTPException(status_code=404, detail="Verse not found at specified location")
    return verse


@app.get("/random", response_model=schemas.SGGSText, summary="Get random verse")
def get_random_verse(db: Session = Depends(get_db)):
    """Get a random verse."""
    repo = SGGSTextRepository(db)
    verse = repo.get_random_sggs_text()
    if not verse:
        raise HTTPException(status_code=404, detail="No verses found in database")
    return verse


# Statistics endpoint
@app.get("/stats/", response_model=schemas.StatsResponse, summary="Get database statistics")
def get_stats(db: Session = Depends(get_db)):
    """Get database statistics."""
    repo = SGGSTextRepository(db)
    return repo.get_stats()


# Data management endpoints
@app.post("/admin/load-data/", summary="Load data from DOCX file")
def load_data(
    file_path: str = Query(..., description="Path to DOCX file"),
    skip_first: int = Query(2, description="Number of initial lines to skip"),
    clear_existing: bool = Query(False, description="Clear existing data before loading"),
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
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")


@app.post("/admin/load-by-page/", summary="Load data by page from DOCX file")
def load_data_by_page(
    file_path: str = Query(..., description="Path to DOCX file"),
    skip_first: int = Query(2, description="Number of initial lines to skip"),
    clear_existing: bool = Query(False, description="Clear existing data before loading"),
    db: Session = Depends(get_db),
):
    """Load SGGS data by page from DOCX file."""
    try:
        loader = SGGSDataLoader(db)
        
        if clear_existing:
            loader.clear_database()
            
        count = loader.load_by_page(file_path, skip_first)
        return {"message": f"Successfully loaded {count} pages", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")


@app.delete("/admin/clear-data/", summary="Clear all data")
def clear_data(db: Session = Depends(get_db)):
    """Clear all data from the database."""
    try:
        loader = SGGSDataLoader(db)
        loader.clear_database()
        return {"message": "Database cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing data: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
