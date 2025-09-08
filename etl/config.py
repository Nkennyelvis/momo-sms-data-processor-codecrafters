"""
Configuration module for ETL pipeline
Handles environment variables, file paths, thresholds, and categories
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for ETL pipeline settings"""
    
    def __init__(self):
        self.setup_paths()
        self.setup_database()
        self.setup_etl_settings()
        self.setup_categories()
        self.setup_validation()
    
    def setup_paths(self):
        """Set up file and directory paths"""
        self.PROJECT_ROOT = Path(__file__).parent.parent
        
        # Input/Output paths
        self.XML_INPUT_PATH = os.getenv('XML_INPUT_PATH', 'data/raw/momo.xml')
        self.JSON_OUTPUT_PATH = os.getenv('JSON_OUTPUT_PATH', 'data/processed/dashboard.json')
        self.LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', 'data/logs/etl.log')
        self.DEAD_LETTER_PATH = os.getenv('DEAD_LETTER_PATH', 'data/logs/dead_letter/')
        
        # Ensure directories exist
        self.ensure_directories()
    
    def setup_database(self):
        """Set up database configuration"""
        self.DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/db.sqlite3')
        self.DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/db.sqlite3')
    
    def setup_etl_settings(self):
        """Set up ETL processing settings"""
        self.BATCH_SIZE = int(os.getenv('BATCH_SIZE', 1000))
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        
        # XML parsing settings
        self.XML_ENCODING = 'utf-8'
        self.XML_NAMESPACE = {}
        
        # Processing settings
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 1  # seconds
    
    def setup_categories(self):
        """Set up transaction categories and mapping rules"""
        categories_str = os.getenv('DEFAULT_CATEGORIES', 'payment,transfer,deposit,withdrawal,airtime,other')
        self.DEFAULT_CATEGORIES = [cat.strip() for cat in categories_str.split(',')]
        
        # Category mapping keywords
        self.CATEGORY_KEYWORDS = {
            'payment': ['pay', 'purchase', 'buy', 'shop', 'merchant'],
            'transfer': ['send', 'transfer', 'remit', 'move'],
            'deposit': ['deposit', 'add', 'top up', 'load', 'credit'],
            'withdrawal': ['withdraw', 'cash out', 'debit', 'subtract'],
            'airtime': ['airtime', 'minutes', 'data', 'bundle', 'recharge'],
            'other': ['fee', 'charge', 'commission', 'tax']
        }
    
    def setup_validation(self):
        """Set up data validation thresholds"""
        self.MIN_TRANSACTION_AMOUNT = float(os.getenv('MIN_TRANSACTION_AMOUNT', 0.01))
        self.MAX_TRANSACTION_AMOUNT = float(os.getenv('MAX_TRANSACTION_AMOUNT', 1000000))
        self.PHONE_NUMBER_LENGTH = int(os.getenv('PHONE_NUMBER_LENGTH', 10))
        
        # Phone number patterns (Uganda format)
        self.PHONE_PATTERNS = [
            r'^\+256\d{9}$',  # International format
            r'^256\d{9}$',    # Without plus
            r'^0\d{9}$',      # Local format
            r'^\d{9}$'        # Without leading zero
        ]
        
        # Date formats to try when parsing
        self.DATE_FORMATS = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y',
            '%m/%d/%Y %H:%M:%S',
            '%m/%d/%Y'
        ]
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            'data/raw',
            'data/processed', 
            'data/logs',
            'data/logs/dead_letter'
        ]
        
        for directory in directories:
            path = self.PROJECT_ROOT / directory
            path.mkdir(parents=True, exist_ok=True)
    
    def get_absolute_path(self, relative_path: str) -> Path:
        """Convert relative path to absolute path from project root"""
        return self.PROJECT_ROOT / relative_path
    
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary for logging/debugging"""
        return {
            'xml_input_path': self.XML_INPUT_PATH,
            'json_output_path': self.JSON_OUTPUT_PATH,
            'log_file_path': self.LOG_FILE_PATH,
            'database_path': self.DATABASE_PATH,
            'batch_size': self.BATCH_SIZE,
            'log_level': self.LOG_LEVEL,
            'categories': self.DEFAULT_CATEGORIES,
            'min_amount': self.MIN_TRANSACTION_AMOUNT,
            'max_amount': self.MAX_TRANSACTION_AMOUNT
        }

# Global config instance
config = Config()
