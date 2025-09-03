"""Database models for SGGS verses."""

from datetime import datetime
import re

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Verse(Base):
    """Model for storing SGGS verses."""

    __tablename__ = "verses"

    id = Column(Integer, primary_key=True, index=True)
    gurmukhi_text = Column(Text, nullable=False, index=True)
    page_number = Column(Integer, nullable=True, index=True)
    line_number = Column(Integer, nullable=True, index=True)
    transliteration = Column(Text, nullable=True)
    translation = Column(Text, nullable=True)
    raag = Column(String(100), nullable=True, index=True)
    author = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Verse(page={self.page_number}, line={self.line_number}, text='{self.gurmukhi_text[:30]}...')>"


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


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
