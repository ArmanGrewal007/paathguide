"""Database operations and CRUD functions."""

from sqlalchemy import and_, distinct, func
from sqlalchemy.orm import Session

from paathguide.db_helper import models, schemas


class VerseRepository:
    """Repository class for verse operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_verse(self, verse: schemas.VerseCreate) -> models.Verse:
        """Create a new verse."""
        db_verse = models.Verse(**verse.model_dump())
        self.db.add(db_verse)
        self.db.commit()
        self.db.refresh(db_verse)
        return db_verse

    def get_verse(self, verse_id: int) -> models.Verse | None:
        """Get a verse by ID."""
        return self.db.query(models.Verse).filter(models.Verse.id == verse_id).first()

    def get_verse_by_page_line(self, page: int, line: int) -> models.Verse | None:
        """Get a verse by page and line number."""
        return (
            self.db.query(models.Verse)
            .filter(and_(models.Verse.page_number == page, models.Verse.line_number == line))
            .first()
        )

    def get_verses(self, skip: int = 0, limit: int = 20) -> list[models.Verse]:
        """Get verses with pagination."""
        return self.db.query(models.Verse).offset(skip).limit(limit).all()

    def search_verses(self, query: schemas.VerseSearchQuery) -> tuple[list[models.Verse], int]:
        """Search verses based on query parameters."""
        db_query = self.db.query(models.Verse)

        # Text search
        if query.query:
            db_query = db_query.filter(models.Verse.gurmukhi_text.contains(query.query))

        # Filters
        if query.page_number:
            db_query = db_query.filter(models.Verse.page_number == query.page_number)

        if query.raag:
            db_query = db_query.filter(models.Verse.raag == query.raag)

        if query.author:
            db_query = db_query.filter(models.Verse.author == query.author)

        # Get total count before pagination
        total = db_query.count()

        # Apply pagination
        verses = db_query.offset(query.offset).limit(query.limit).all()

        return verses, total

    def get_page_content(self, page_number: int) -> list[models.Verse]:
        """Get all verses from a specific page."""
        return (
            self.db.query(models.Verse)
            .filter(models.Verse.page_number == page_number)
            .order_by(models.Verse.line_number)
            .all()
        )

    def get_surrounding_verses(self, verse_id: int, context: int = 3) -> list[models.Verse]:
        """Get verses around a specific verse for context."""
        verse = self.get_verse(verse_id)
        if not verse or verse.line_number is None:
            return []

        min_line = max(1, verse.line_number - context)
        max_line = verse.line_number + context

        return (
            self.db.query(models.Verse)
            .filter(
                and_(
                    models.Verse.page_number == verse.page_number,
                    models.Verse.line_number.between(min_line, max_line),
                )
            )
            .order_by(models.Verse.line_number)
            .all()
        )

    def get_random_verse(self) -> models.Verse | None:
        """Get a random verse."""
        return self.db.query(models.Verse).order_by(func.random()).first()

    def update_verse(self, verse_id: int, verse_update: schemas.VerseUpdate) -> models.Verse | None:
        """Update a verse."""
        db_verse = self.get_verse(verse_id)
        if not db_verse:
            return None

        update_data = verse_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_verse, field, value)

        self.db.commit()
        self.db.refresh(db_verse)
        return db_verse

    def delete_verse(self, verse_id: int) -> bool:
        """Delete a verse."""
        db_verse = self.get_verse(verse_id)
        if not db_verse:
            return False

        self.db.delete(db_verse)
        self.db.commit()
        return True

    def get_stats(self) -> schemas.StatsResponse:
        """Get database statistics."""
        total_verses = self.db.query(models.Verse).count()
        total_pages = self.db.query(distinct(models.Verse.page_number)).count()
        verses_with_translations = (
            self.db.query(models.Verse).filter(models.Verse.translation.isnot(None)).count()
        )
        verses_with_transliterations = (
            self.db.query(models.Verse).filter(models.Verse.transliteration.isnot(None)).count()
        )
        unique_raags = (
            self.db.query(distinct(models.Verse.raag)).filter(models.Verse.raag.isnot(None)).count()
        )
        unique_authors = (
            self.db.query(distinct(models.Verse.author))
            .filter(models.Verse.author.isnot(None))
            .count()
        )

        return schemas.StatsResponse(
            total_verses=total_verses,
            total_pages=total_pages,
            verses_with_translations=verses_with_translations,
            verses_with_transliterations=verses_with_transliterations,
            unique_raags=unique_raags,
            unique_authors=unique_authors,
        )

    def bulk_create_verses(self, verses: list[schemas.VerseCreate]) -> list[models.Verse]:
        """Create multiple verses efficiently."""
        db_verses = [models.Verse(**verse.model_dump()) for verse in verses]
        self.db.add_all(db_verses)
        self.db.commit()
        return db_verses
