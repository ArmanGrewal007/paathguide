"""Database models for SGGS verses with FTS5 support."""

from datetime import datetime
import re
import sqlite3

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class SGGSText(Base):
    """Model for storing SGGS text with FTS5 support."""

    __tablename__ = "sggs_text"

    id = Column(Integer, primary_key=True, index=True)
    gurmukhi_text = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True, index=True)
    line_number = Column(Integer, nullable=True, index=True)
    transliteration = Column(Text, nullable=True)
    translation = Column(Text, nullable=True)
    raag = Column(String(100), nullable=True, index=True)
    author = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SGGSText(page={self.page_number}, line={self.line_number}, text='{self.gurmukhi_text[:30]}...')>"


def parse_verse_line(line: str) -> dict:
    """
    Parse a line like 'ਆਦਿ ਸਚੁ ਜੁਗਾਦਿ ਸਚੁ ॥ (1-4)' into components.

    Args:
        line: Raw line from the document

    Returns:
        ```python
        {
            "gurmukhi_text": "ਆਦਿ ਸਚੁ ਜੁਗਾਦਿ ਸਚੁ ॥",
            "page_number": 1,
            "line_number": 4
        }
        ```
    """
    # Pattern to match text followed by (page-line)
    pattern = r"^(.+?)\s*\((\d+)-(\d+)\)\s*$"
    match = re.match(pattern, line.strip())

    if match:
        text = match.group(1).strip()
        page = int(match.group(2))
        line_num = int(match.group(3))

        return {"gurmukhi_text": text, "page_number": page, "line_number": line_num}
    else:
        # If pattern doesn't match, treat as plain text
        return {"gurmukhi_text": line.strip(), "page_number": None, "line_number": None}


# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./sggs.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_fts_table():
    """Create FTS5 virtual table for full-text search."""
    with engine.connect() as connection:
        # Drop old tables if they exist
        try:
            connection.execute(text("DROP TABLE IF EXISTS verses"))
            connection.execute(text("DROP TABLE IF EXISTS sggs_fts"))
            connection.commit()
        except Exception as e:
            print(f"Note: Could not drop old tables: {e}")
        
        # Create FTS5 virtual table
        fts_sql = text("""
        CREATE VIRTUAL TABLE IF NOT EXISTS sggs_fts USING fts5(
            gurmukhi_text,
            page_number UNINDEXED,
            line_number UNINDEXED,
            transliteration,
            translation,
            raag UNINDEXED,
            author UNINDEXED,
            content='sggs_text',
            content_rowid='id'
        )
        """)
        connection.execute(fts_sql)
        
        # Create triggers to keep FTS table in sync
        triggers_sql = [
            text("""
            CREATE TRIGGER IF NOT EXISTS sggs_fts_insert AFTER INSERT ON sggs_text
            BEGIN
                INSERT INTO sggs_fts(rowid, gurmukhi_text, page_number, line_number, transliteration, translation, raag, author)
                VALUES (new.id, new.gurmukhi_text, new.page_number, new.line_number, new.transliteration, new.translation, new.raag, new.author);
            END
            """),
            text("""
            CREATE TRIGGER IF NOT EXISTS sggs_fts_delete AFTER DELETE ON sggs_text
            BEGIN
                INSERT INTO sggs_fts(sggs_fts, rowid, gurmukhi_text, page_number, line_number, transliteration, translation, raag, author)
                VALUES ('delete', old.id, old.gurmukhi_text, old.page_number, old.line_number, old.transliteration, old.translation, old.raag, old.author);
            END
            """),
            text("""
            CREATE TRIGGER IF NOT EXISTS sggs_fts_update AFTER UPDATE ON sggs_text
            BEGIN
                INSERT INTO sggs_fts(sggs_fts, rowid, gurmukhi_text, page_number, line_number, transliteration, translation, raag, author)
                VALUES ('delete', old.id, old.gurmukhi_text, old.page_number, old.line_number, old.transliteration, old.translation, old.raag, old.author);
                INSERT INTO sggs_fts(rowid, gurmukhi_text, page_number, line_number, transliteration, translation, raag, author)
                VALUES (new.id, new.gurmukhi_text, new.page_number, new.line_number, new.transliteration, new.translation, new.raag, new.author);
            END
            """)
        ]
        
        for trigger_sql in triggers_sql:
            connection.execute(trigger_sql)
        
        connection.commit()
        print("FTS5 table and triggers created successfully")


def create_tables():
    """Create all database tables including FTS5."""
    Base.metadata.create_all(bind=engine)
    create_fts_table()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
