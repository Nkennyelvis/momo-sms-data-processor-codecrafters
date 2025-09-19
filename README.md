# MoMo SMS Data Processor

## Team Information
**Team Name:** CodeCrafters  
**Project:** Enterprise-level Fullstack MoMo SMS Data Processing Application

### Team Members
- **Elvis Kenny Nsengimana Ishema**
- **Lydivine Umutesi Munyampundu**
- **Seth Iradukunda**

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
![alt text](image.png)

## Scrum Board – CodeCrafters
**To Do**
Complete ETL pipeline (parse → clean → categorize → load → export JSON)
Implement RESTful API endpoints (/transactions, /analytics)
Write advanced unit + integration tests
Performance optimization for ETL & database
 
**In Progress**
-FastAPI development (Elvis)
-Frontend dashboard enhancements (Lydivine)
-DevOps setup & CI/CD (Seth)

**Done**

-Repository setup
-Initial project structure scaffold
-Basic XML parsing prototype

## Project Structure
```
.
├── README.md                         # Setup, run, overview
├── .env.example                      # DATABASE_URL or path to SQLite
├── requirements.txt                  # lxml/ElementTree, dateutil, (FastAPI optional)
├── index.html                        # Dashboard entry (static)
├── docs/                             # WEEK 2: Database design documentation
│   ├── erd_design_document.md        # ERD design and business rationale
│   └── data_dictionary.md            # Complete table definitions and queries
├── database/                         # WEEK 2: Database implementation
│   └── database_setup.sql            # MySQL DDL script with sample data
├── examples/                         # WEEK 2: JSON schemas and examples
│   └── json_schemas.json             # API response formats and data mapping
├── web/
│   ├── styles.css                    # Dashboard styling
│   ├── chart_handler.js              # Fetch + render charts/tables
│   └── assets/                       # Images/icons (optional)
├── data/
│   ├── raw/                          # Provided XML input (git-ignored)
│   │   └── momo.xml
│   ├── processed/                    # Cleaned/derived outputs for frontend
│   │   └── dashboard.json            # Aggregates the dashboard reads
│   ├── db.sqlite3                    # SQLite DB file (Week 1)
│   └── logs/
│       ├── etl.log                   # Structured ETL logs
│       └── dead_letter/              # Unparsed/ignored XML snippets
├── etl/
│   ├── __init__.py
│   ├── config.py                     # File paths, thresholds, categories
│   ├── parse_xml.py                  # XML parsing (ElementTree/lxml)
│   ├── clean_normalize.py            # Amounts, dates, phone normalization
│   ├── categorize.py                 # Simple rules for transaction types
│   ├── load_db.py                    # Create tables + upsert to database
│   └── run.py                        # CLI: parse -> clean -> categorize -> load -> export JSON
├── api/                              # Optional (bonus)
│   ├── __init__.py
│   ├── app.py                        # Minimal FastAPI with /transactions, /analytics
│   ├── db.py                         # Database connection helpers (MySQL/SQLite)
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

## Week 2: Database Design and Implementation

### Database Architecture

Based on our analysis of MoMo SMS transaction patterns, we've designed a comprehensive MySQL database that supports:

- **Transaction Processing**: Efficient storage and retrieval of mobile money transactions
- **User Management**: Complete user profiles with privacy and security controls
- **Category Classification**: Flexible transaction categorization system
- **System Monitoring**: Comprehensive logging and audit trails
- **Performance Optimization**: Strategic indexing and query optimization
- **Data Integrity**: Robust constraints and validation rules

### Core Database Entities

1. **users** - Mobile money account holders
2. **transactions** - Main transaction records with full details
3. **transaction_categories** - Classification system for transaction types
4. **system_logs** - Processing activities and error tracking
5. **user_transaction_roles** - Many-to-many user-transaction relationships
6. **transaction_tags** - Flexible tagging system
7. **transaction_tag_assignments** - Tag assignments to transactions

### Database Setup

```bash
# Install MySQL 8.0+
# Create database and run setup script
mysql -u root -p < database/database_setup.sql

# Verify installation
mysql -u root -p -e "USE momo_sms_db; SHOW TABLES;"
```

### Key Features

- **ACID Compliance**: Full transaction integrity with MySQL InnoDB
- **Referential Integrity**: Complete foreign key constraint enforcement
- **Performance Indexes**: Optimized for high-volume transaction processing
- **JSON Support**: Flexible data storage for evolving requirements
- **Audit Trail**: Complete tracking of all data modifications
- **Security**: Multi-level access control and data validation

### Documentation

- **ERD Design Document**: [`docs/erd_design_document.md`](docs/erd_design_document.md) - Complete design rationale and business requirements analysis
- **Data Dictionary**: [`docs/data_dictionary.md`](docs/data_dictionary.md) - Detailed table definitions, constraints, and sample queries
- **JSON Schemas**: [`examples/json_schemas.json`](examples/json_schemas.json) - API response formats and data serialization examples

### Sample Queries

```sql
-- Get user transaction history
SELECT * FROM v_transaction_details 
WHERE sender_phone = '+250788123456' 
OR receiver_phone = '+250788123456'
ORDER BY transaction_date DESC;

-- Daily transaction analytics
SELECT DATE(transaction_date) as date,
       COUNT(*) as transaction_count,
       SUM(amount) as total_volume,
       AVG(amount) as avg_amount
FROM transactions 
WHERE status = 'SUCCESS'
GROUP BY DATE(transaction_date)
ORDER BY date DESC;
```

### Performance Optimizations

- **Composite Indexes**: Multi-column indexes for complex queries
- **Partitioning Ready**: Transaction table designed for date-based partitioning
- **View Optimization**: Pre-joined views for common query patterns
- **JSON Indexing**: Efficient querying of JSON fields in system logs

---

## Development Workflow

1. **Feature Development**: Create feature branches from `main`
2. **Code Review**: Submit pull requests for code review
3. **Testing**: Ensure all tests pass before merging
4. **Documentation**: Update documentation for new features
5. **Database Changes**: All schema changes must include migration scripts
