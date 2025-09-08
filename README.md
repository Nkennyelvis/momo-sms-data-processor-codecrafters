# MoMo SMS Data Processor

## Team Information
**Team Name:** CodeCrafters  
**Project:** Enterprise-level Fullstack MoMo SMS Data Processing Application

### Team Members
- **Elvis Kenny Nsengimana Ishema** - Team Lead & Backend Developer
- **Lydivine Umutesi Munyampundu** - Frontend Developer & UI/UX Designer
- **Seth Iradukunda** - Database Engineer & DevOps Specialist

## Project Description
This enterprise-level fullstack application processes Mobile Money (MoMo) SMS data in XML format, cleans and categorizes the data, stores it in a relational database, and provides a frontend interface for data analysis and visualization.

### Key Features
- XML data parsing and processing
- Data cleaning and normalization
- Transaction categorization
- SQLite database storage
- Interactive web dashboard
- RESTful API (optional)
- Comprehensive logging and error handling

## System Architecture
[System Architecture Diagram Link - To be added]

## Scrum Board
[Scrum Board Link - To be added]

## Project Structure
```
.
├── README.md                         # Setup, run, overview
├── .env.example                      # DATABASE_URL or path to SQLite
├── requirements.txt                  # lxml/ElementTree, dateutil, (FastAPI optional)
├── index.html                        # Dashboard entry (static)
├── web/
│   ├── styles.css                    # Dashboard styling
│   ├── chart_handler.js              # Fetch + render charts/tables
│   └── assets/                       # Images/icons (optional)
├── data/
│   ├── raw/                          # Provided XML input (git-ignored)
│   │   └── momo.xml
│   ├── processed/                    # Cleaned/derived outputs for frontend
│   │   └── dashboard.json            # Aggregates the dashboard reads
│   ├── db.sqlite3                    # SQLite DB file
│   └── logs/
│       ├── etl.log                   # Structured ETL logs
│       └── dead_letter/              # Unparsed/ignored XML snippets
├── etl/
│   ├── __init__.py
│   ├── config.py                     # File paths, thresholds, categories
│   ├── parse_xml.py                  # XML parsing (ElementTree/lxml)
│   ├── clean_normalize.py            # Amounts, dates, phone normalization
│   ├── categorize.py                 # Simple rules for transaction types
│   ├── load_db.py                    # Create tables + upsert to SQLite
│   └── run.py                        # CLI: parse -> clean -> categorize -> load -> export JSON
├── api/                              # Optional (bonus)
│   ├── __init__.py
│   ├── app.py                        # Minimal FastAPI with /transactions, /analytics
│   ├── db.py                         # SQLite connection helpers
│   └── schemas.py                    # Pydantic response models
├── scripts/
│   ├── run_etl.sh                    # python etl/run.py --xml data/raw/momo.xml
│   ├── export_json.sh                # Rebuild data/processed/dashboard.json
│   └── serve_frontend.sh             # python -m http.server 8000 (or Flask static)
└── tests/
    ├── test_parse_xml.py             # Small unit tests
    ├── test_clean_normalize.py
    └── test_categorize.py
```

## Setup and Installation

### Prerequisites
- Python 3.8+
- Git
- Web browser

### Installation
1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd momo-sms-data-processor
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Usage

### Running the ETL Pipeline
```bash
# Run the complete ETL process
./scripts/run_etl.sh

# Or run with Python
python etl/run.py --xml data/raw/momo.xml
```

### Starting the Frontend
```bash
# Serve the static frontend
./scripts/serve_frontend.sh

# Or manually
python -m http.server 8000
```

### API (Optional)
```bash
# Start the FastAPI server
uvicorn api.app:app --reload --port 8001
```

## Development Workflow

1. **Feature Development**: Create feature branches from `main`
2. **Code Review**: Submit pull requests for code review
3. **Testing**: Ensure all tests pass before merging
4. **Documentation**: Update documentation for new features

## Testing
```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_parse_xml.py
```

## Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Contact
- Project Repository: [GitHub Repository Link]
- Scrum Board: [Scrum Board Link]
- Architecture Diagram: [Architecture Diagram Link]
