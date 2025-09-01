"""Updated cleaning module that integrates with the new SGGS database system."""

import re

from docx import Document

from .data_loader import SGGSDataLoader
from .models import SessionLocal, create_tables


def clean_stt_text(text: str) -> str:
    """Clean speech-to-text output for better matching."""
    text = re.sub(r"(.)\1{2,}", r"\1", text)  # collapse repeated letters
    text = re.sub(r"(ਸ਼ਿ\s*){2,}", "ਸ਼ਿ", text)  # collapse repeated 'shi shi'
    text = re.sub(r"\s+", " ", text).strip()  # normalize spaces
    return text


def load_sggs_data():
    """Load SGGS data from DOCX into database."""
    # Create database tables
    create_tables()

    # Load data
    db = SessionLocal()
    try:
        loader = SGGSDataLoader(db)
        count = loader.load_from_docx("SGGS-Gurm-SBS-Uni with page line numbers.docx")
        print(f"Successfully loaded {count} verses into database")
    finally:
        db.close()


def main():
    """Main function for testing and data loading."""
    # Test the old functionality
    doc = Document("SGGS-Gurm-SBS-Uni with page line numbers.docx")

    lines = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            lines.append(text)

    lines = lines[2:]  # skip the first two
    print("Total lines:", len(lines))
    print("Sample:", lines[:5])

    # Test STT cleaning
    txt = " ਗੁਰ ਪੱੱਾਦ ਜਾਪ ਆਦ ਸਾਚ ਜਗਾਦ ਸਾਚ ਹਿ ਸਾਚ ਨਾਨਕ ਹੋ ਸੀਬੀ ਸਾਚ ਸਚ਼ਿ ਸ਼ਿ ਸ਼ਿ ਸ਼ਿ ਸ਼ਿ"
    print("Original STT:", txt)
    print("Cleaned STT:", clean_stt_text(txt))

    # Load into database
    load_sggs_data()


if __name__ == "__main__":
    main()
