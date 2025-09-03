"""Database operations and CRUD functions with FTS5 support."""

from sqlalchemy import and_, distinct, func, text
from sqlalchemy.orm import Session

from paathguide.db import models, schemas


class SGGSTextRepository:
    """Repository class for SGGS text operations with FTS5 support."""

    def __init__(self, db: Session):
        self.db = db

    def create_sggs_text(self, sggs_text: schemas.SGGSTextCreate) -> models.SGGSText:
        """Create a new SGGS text entry."""
        db_sggs_text = models.SGGSText(**sggs_text.model_dump())
        self.db.add(db_sggs_text)
        self.db.commit()
        self.db.refresh(db_sggs_text)
        return db_sggs_text

    def get_sggs_text(self, text_id: int) -> models.SGGSText | None:
        """Get SGGS text by ID."""
        return self.db.query(models.SGGSText).filter(models.SGGSText.id == text_id).first()

    def get_sggs_text_by_page_line(self, page: int, line: int) -> models.SGGSText | None:
        """Get SGGS text by page and line number."""
        return (
            self.db.query(models.SGGSText)
            .filter(and_(models.SGGSText.page_number == page, models.SGGSText.line_number == line))
            .first()
        )

    def get_sggs_texts(self, skip: int = 0, limit: int = 20) -> list[models.SGGSText]:
        """Get SGGS texts with pagination."""
        return self.db.query(models.SGGSText).offset(skip).limit(limit).all()

    def search_with_fts(self, query: str, skip: int = 0, limit: int = 20) -> tuple[list[models.SGGSText], int]:
        """
        Search SGGS texts using FTS5 full-text search.
        
        Args:
            query: Search query string
            skip: Number of results to skip for pagination
            limit: Maximum number of results to return
            
        Returns:
            Tuple of (results, total_count)
        """
        # Use FTS5 search with ranking - get IDs first
        search_sql = text("""
            SELECT rowid
            FROM sggs_fts
            WHERE sggs_fts MATCH :query
            ORDER BY rank
            LIMIT :limit OFFSET :skip
        """)
        
        count_sql = text("""
            SELECT COUNT(*)
            FROM sggs_fts
            WHERE sggs_fts MATCH :query
        """)
        
        # Get IDs from FTS
        result = self.db.execute(search_sql, {"query": query, "limit": limit, "skip": skip})
        ids = [row[0] for row in result.fetchall()]
        
        # Get total count
        count_result = self.db.execute(count_sql, {"query": query})
        total = count_result.scalar() or 0
        
        # Get actual objects from main table
        if ids:
            sggs_texts = self.db.query(models.SGGSText).filter(models.SGGSText.id.in_(ids)).all()
            # Maintain the order from FTS search
            sggs_texts_dict = {text.id: text for text in sggs_texts}
            ordered_results = [sggs_texts_dict[id_] for id_ in ids if id_ in sggs_texts_dict]
        else:
            ordered_results = []
        
        return ordered_results, total

    def search_sggs_texts(self, query: schemas.VerseSearchQuery) -> tuple[list[models.SGGSText], int]:
        """Search SGGS texts based on query parameters."""
        # If we have a text query, use FTS5
        if query.query:
            # Build FTS query with filters
            fts_query = query.query
            
            # Use SQL to apply filters efficiently
            search_sql = text("""
                SELECT st.id
                FROM sggs_text st
                JOIN sggs_fts fts ON st.id = fts.rowid
                WHERE sggs_fts MATCH :query
                AND (:page_number IS NULL OR st.page_number = :page_number)
                AND (:raag IS NULL OR st.raag = :raag)
                AND (:author IS NULL OR st.author = :author)
                ORDER BY rank
                LIMIT :limit OFFSET :skip
            """)
            
            count_sql = text("""
                SELECT COUNT(*)
                FROM sggs_text st
                JOIN sggs_fts fts ON st.id = fts.rowid
                WHERE sggs_fts MATCH :query
                AND (:page_number IS NULL OR st.page_number = :page_number)
                AND (:raag IS NULL OR st.raag = :raag)
                AND (:author IS NULL OR st.author = :author)
            """)
            
            params = {
                "query": fts_query,
                "page_number": query.page_number,
                "raag": query.raag,
                "author": query.author,
                "limit": query.limit,
                "skip": query.offset
            }
            
            # Get IDs from FTS
            result = self.db.execute(search_sql, params)
            ids = [row[0] for row in result.fetchall()]
            
            # Get total count
            count_result = self.db.execute(count_sql, params)
            total = count_result.scalar() or 0
            
            # Get actual objects from main table in order
            if ids:
                sggs_texts = self.db.query(models.SGGSText).filter(models.SGGSText.id.in_(ids)).all()
                # Maintain the order from FTS search
                sggs_texts_dict = {text.id: text for text in sggs_texts}
                ordered_results = [sggs_texts_dict[id_] for id_ in ids if id_ in sggs_texts_dict]
            else:
                ordered_results = []
            
            return ordered_results, total
        else:
            # If no text query, use traditional database queries
            db_query = self.db.query(models.SGGSText)

            # Filters
            if query.page_number:
                db_query = db_query.filter(models.SGGSText.page_number == query.page_number)
            if query.raag:
                db_query = db_query.filter(models.SGGSText.raag == query.raag)
            if query.author:
                db_query = db_query.filter(models.SGGSText.author == query.author)

            # Get total count before pagination
            total = db_query.count()

            # Apply pagination
            sggs_texts = db_query.offset(query.offset).limit(query.limit).all()

            return sggs_texts, total

    def get_page_content(self, page_number: int) -> list[models.SGGSText]:
        """Get all SGGS texts from a specific page."""
        return (
            self.db.query(models.SGGSText)
            .filter(models.SGGSText.page_number == page_number)
            .order_by(models.SGGSText.line_number)
            .all()
        )

    def get_surrounding_texts(self, text_id: int, context: int = 3) -> list[models.SGGSText]:
        """Get SGGS texts around a specific text for context."""
        sggs_text = self.get_sggs_text(text_id)
        if not sggs_text or sggs_text.line_number is None:
            return []

        min_line = max(1, sggs_text.line_number - context) # type: ignore
        max_line = sggs_text.line_number + context

        return (
            self.db.query(models.SGGSText)
            .filter(
                and_(
                    models.SGGSText.page_number == sggs_text.page_number,
                    models.SGGSText.line_number.between(min_line, max_line),
                )
            )
            .order_by(models.SGGSText.line_number)
            .all()
        )

    def get_random_sggs_text(self) -> models.SGGSText | None:
        """Get a random SGGS text."""
        return self.db.query(models.SGGSText).order_by(func.random()).first()

    def update_sggs_text(self, text_id: int, text_update: schemas.SGGSTextUpdate) -> models.SGGSText | None:
        """Update SGGS text."""
        db_sggs_text = self.get_sggs_text(text_id)
        if not db_sggs_text:
            return None

        update_data = text_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_sggs_text, field, value)

        self.db.commit()
        self.db.refresh(db_sggs_text)
        return db_sggs_text

    def delete_sggs_text(self, text_id: int) -> bool:
        """Delete SGGS text."""
        db_sggs_text = self.get_sggs_text(text_id)
        if not db_sggs_text:
            return False

        self.db.delete(db_sggs_text)
        self.db.commit()
        return True

    def get_stats(self) -> schemas.StatsResponse:
        """Get database statistics."""
        total_verses = self.db.query(models.SGGSText).count()
        total_pages = self.db.query(distinct(models.SGGSText.page_number)).count()
        count_non_null = lambda field: self.db.query(models.SGGSText).filter(field.isnot(None)).count()
        count_unique_non_null = lambda field: self.db.query(distinct(field)).filter(field.isnot(None)).count()

        verses_with_translations = count_non_null(models.SGGSText.translation)
        verses_with_transliterations = count_non_null(models.SGGSText.transliteration)
        unique_raags = count_unique_non_null(models.SGGSText.raag)
        unique_authors = count_unique_non_null(models.SGGSText.author)

        return schemas.StatsResponse(
            total_verses=total_verses,
            total_pages=total_pages,
            verses_with_translations=verses_with_translations,
            verses_with_transliterations=verses_with_transliterations,
            unique_raags=unique_raags,
            unique_authors=unique_authors,
        )

    def bulk_create_sggs_texts(self, sggs_texts: list[schemas.SGGSTextCreate]) -> list[models.SGGSText]:
        """Create multiple SGGS texts efficiently."""
        db_sggs_texts = [models.SGGSText(**sggs_text.model_dump()) for sggs_text in sggs_texts]
        self.db.add_all(db_sggs_texts)
        self.db.commit()
        return db_sggs_texts

