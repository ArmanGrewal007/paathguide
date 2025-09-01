# SGGS API - Complete Backend Solution

A FastAPI-based backend for Shri Guru Granth Sahib with search, navigation, and data management capabilities.

## Features

- 🔍 **Full-text search** in Gurmukhi
- 📖 **Page/line navigation**
- 🎲 **Random verse** (Hukamnama style)
- 📊 **Database statistics**
- 🔧 **Data management** (load from DOCX, clear, etc.)
- 🎯 **Context retrieval** (surrounding verses)
- 🌐 **RESTful API** with OpenAPI documentation

## Project Structure

```
paathguide/
├── paathguide/
│   ├── __init__.py
│   ├── models.py          # SQLAlchemy database models
│   ├── schemas.py         # Pydantic request/response schemas  
│   ├── repository.py      # Database operations (CRUD)
│   ├── data_loader.py     # DOCX data loading utilities
│   ├── api.py            # FastAPI application
│   ├── cli.py            # Command-line interface
│   └── cleaning.py       # Text cleaning utilities
├── run_server.py         # Server startup script
├── test_api.py          # Basic functionality tests
└── README.md
```

## Installation & Setup

poetry run python -m paathguide.cli load-data --file-path="/Users/armangrewal/Desktop/Research/paathguide/SGGS-Gurm-SBS-Uni with page line numbers.docx"

1. **Install dependencies** (already done):

   ```bash
   poetry install
   ```
2. **Initialize database**:

   ```bash
   poetry run python -c "from paathguide.models import create_tables; create_tables()"
   ```
3. **Load compelte data** (takes about 10 seconds):

   ```bash
   poetry run python -m paathguide.cli load-data --file-path="./SGGS-Gurm-SBS-Uni with page line numbers.docx"
   ```

## Usage

### 1. Load Your SGGS Data

```bash
# Load from your DOCX file
poetry run python -c "
from paathguide.models import create_tables, SessionLocal
from paathguide.data_loader import SGGSDataLoader
create_tables()
db = SessionLocal()
loader = SGGSDataLoader(db)
count = loader.load_from_docx('SGGS-Gurm-SBS-Uni with page line numbers.docx')
print(f'Loaded {count} verses')
db.close()
"
```

### 2. Start the API Server

```bash
# Start the FastAPI server
poetry run python run_server.py
```

The API will be available at:

- **API**: http://localhost:8000
- **Interactive docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. Test the API

```bash
# Run basic functionality tests
poetry run python test_api.py
```

## API Endpoints

### Core Operations

- `GET /` - Health check
- `GET /verses/` - List verses (paginated)
- `GET /verses/{id}` - Get specific verse
- `POST /verses/` - Create new verse
- `PUT /verses/{id}` - Update verse
- `DELETE /verses/{id}` - Delete verse

### Search & Navigation

- `GET /search/?q=text` - Search verses
- `POST /search/` - Advanced search with filters
- `GET /pages/{page_number}` - Get all verses from a page
- `GET /verses/page/{page}/line/{line}` - Get verse by location
- `GET /verses/{id}/context` - Get surrounding verses
- `GET /random` - Random verse (Hukamnama)

### Statistics & Admin

- `GET /stats` - Database statistics
- `POST /admin/load-data` - Load data from DOCX
- `POST /admin/load-sample` - Load sample data
- `DELETE /admin/clear-data` - Clear all data

## API Examples

### Search for verses containing "ਸਚੁ"

```bash
curl "http://localhost:8000/search/?q=ਸਚੁ&limit=5"
```

### Get page 1 content

```bash
curl "http://localhost:8000/pages/1"
```

### Get random verse

```bash
curl "http://localhost:8000/random"
```

### Get verse context

```bash
curl "http://localhost:8000/verses/1/context?context=3"
```

## Data Model

Each verse contains:

- `id`: Unique identifier
- `gurmukhi_text`: The Gurmukhi text
- `page_number`: Page in SGGS
- `line_number`: Line on the page
- `transliteration`: Roman script (optional)
- `translation`: English translation (optional)
- `raag`: Musical mode (optional)
- `author`: Guru/Bhagat (optional)
- `created_at`: Timestamp

## Integration with Speech Recognition

The cleaning utilities can be used with your audio transcription work:

```python
from paathguide.cleaning import clean_stt_text

# Clean speech-to-text output
raw_stt = "ਗੁਰ ਪੱੱਾਦ ਸ਼ਿ ਸ਼ਿ ਸ਼ਿ"
cleaned = clean_stt_text(raw_stt)  # "ਗੁਰ ਪਾਦ ਸ਼ਿ"

# Then search for matches
# Use the search API to find closest verses
```

## Next Steps

1. **Load your full SGGS data** from the DOCX file
2. **Add translations/transliterations** if you have them
3. **Integrate with your audio work** for speech recognition
4. **Deploy to production** (consider PostgreSQL for better performance)
5. **Add authentication** if needed
6. **Create a frontend** (React, Vue, etc.)

## Development

- **Add new endpoints**: Extend `paathguide/api.py`
- **Modify data model**: Update `paathguide/models.py` and `paathguide/schemas.py`
- **Add business logic**: Extend `paathguide/repository.py`
- **Custom data loading**: Modify `paathguide/data_loader.py`

## Database

- **Development**: SQLite (`sggs.db` file)
- **Production**: Consider PostgreSQL for better full-text search

The database is automatically created when you first run the application.
