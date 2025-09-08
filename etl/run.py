"""
ETL Pipeline Runner
Main orchestration script for the complete MoMo SMS data processing pipeline
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from etl.config import config
from etl.parse_xml import XMLParser
from etl.clean_normalize import DataCleaner
from etl.categorize import TransactionCategorizer
from etl.load_db import DatabaseLoader

# Configure logging
def setup_logging(log_level: str = 'INFO'):
    """Set up logging configuration"""
    log_path = config.get_absolute_path(config.LOG_FILE_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        handlers=[file_handler, console_handler]
    )

logger = logging.getLogger(__name__)

class ETLPipeline:
    """Main ETL pipeline orchestrator"""
    
    def __init__(self, xml_file: str = None, output_file: str = None, verbose: bool = False):
        self.xml_file = xml_file or config.XML_INPUT_PATH
        self.output_file = output_file or config.JSON_OUTPUT_PATH
        self.verbose = verbose
        self.run_id = f"etl_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Pipeline statistics
        self.stats = {
            'start_time': None,
            'end_time': None,
            'xml_parsed': 0,
            'data_cleaned': 0,
            'data_categorized': 0,
            'data_loaded': 0,
            'errors': 0,
            'run_id': self.run_id
        }
    
    def run(self) -> Dict[str, Any]:
        """Execute the complete ETL pipeline"""
        try:
            logger.info(f"Starting ETL pipeline run: {self.run_id}")
            logger.info(f"Input file: {self.xml_file}")
            logger.info(f"Output file: {self.output_file}")
            
            self.stats['start_time'] = datetime.now().isoformat()
            
            # Step 1: Parse XML data
            logger.info("Step 1: Parsing XML data...")
            raw_transactions = self._parse_xml()
            if not raw_transactions:
                logger.error("No data to process - XML parsing returned no results")
                return self._finalize_run(success=False, error="No data parsed from XML")
            
            self.stats['xml_parsed'] = len(raw_transactions)
            logger.info(f"Parsed {len(raw_transactions)} transactions from XML")
            
            # Step 2: Clean and normalize data
            logger.info("Step 2: Cleaning and normalizing data...")
            cleaned_transactions = self._clean_data(raw_transactions)
            if not cleaned_transactions:
                logger.error("No data left after cleaning")
                return self._finalize_run(success=False, error="No data survived cleaning process")
            
            self.stats['data_cleaned'] = len(cleaned_transactions)
            logger.info(f"Cleaned {len(cleaned_transactions)} transactions")
            
            # Step 3: Categorize transactions
            logger.info("Step 3: Categorizing transactions...")
            categorized_transactions = self._categorize_data(cleaned_transactions)
            
            self.stats['data_categorized'] = len(categorized_transactions)
            logger.info(f"Categorized {len(categorized_transactions)} transactions")
            
            # Step 4: Load data to database
            logger.info("Step 4: Loading data to database...")
            load_results = self._load_to_database(categorized_transactions)
            
            self.stats['data_loaded'] = load_results.get('loaded', 0)
            self.stats['errors'] = load_results.get('failed', 0)
            logger.info(f"Loaded {self.stats['data_loaded']} transactions to database")
            
            # Step 5: Export dashboard data
            logger.info("Step 5: Exporting dashboard data...")
            self._export_dashboard_data()
            
            logger.info("ETL pipeline completed successfully!")
            return self._finalize_run(success=True)
            
        except Exception as e:
            logger.error(f"ETL pipeline failed: {e}")
            return self._finalize_run(success=False, error=str(e))
    
    def _parse_xml(self) -> list:
        """Parse XML data using XMLParser"""
        try:
            parser = XMLParser(self.xml_file)
            
            # Validate XML structure first
            if not parser.validate_xml_structure():
                raise ValueError("Invalid XML structure")
            
            transactions = parser.parse_file()
            
            if self.verbose:
                parser_stats = parser.get_stats()
                logger.info(f"XML Parser Stats: {parser_stats}")
            
            return transactions
            
        except Exception as e:
            logger.error(f"XML parsing failed: {e}")
            raise
    
    def _clean_data(self, transactions: list) -> list:
        """Clean and normalize data using DataCleaner"""
        try:
            cleaner = DataCleaner()
            cleaned_transactions = cleaner.clean_transactions(transactions)
            
            if self.verbose:
                cleaning_stats = cleaner.get_cleaning_stats()
                logger.info(f"Data Cleaning Stats: {cleaning_stats}")
                
                # Export validation errors if any
                if cleaner.validation_errors:
                    cleaner.export_validation_errors()
            
            return cleaned_transactions
            
        except Exception as e:
            logger.error(f"Data cleaning failed: {e}")
            raise
    
    def _categorize_data(self, transactions: list) -> list:
        """Categorize transactions using TransactionCategorizer"""
        try:
            categorizer = TransactionCategorizer()
            categorized_transactions = categorizer.categorize_transactions(transactions)
            
            if self.verbose:
                category_stats = categorizer.get_category_stats()
                logger.info(f"Categorization Stats: {category_stats}")
            
            return categorized_transactions
            
        except Exception as e:
            logger.error(f"Transaction categorization failed: {e}")
            raise
    
    def _load_to_database(self, transactions: list) -> Dict[str, Any]:
        """Load transactions to database using DatabaseLoader"""
        try:
            with DatabaseLoader() as db_loader:
                # Create tables if they don't exist
                db_loader.create_tables()
                
                # Create ETL run log
                db_loader.create_etl_run_log(self.run_id, self.xml_file)
                
                # Load transactions
                load_results = db_loader.load_transactions(transactions, self.run_id)
                
                return load_results
                
        except Exception as e:
            logger.error(f"Database loading failed: {e}")
            raise
    
    def _export_dashboard_data(self):
        """Export data for dashboard consumption"""
        try:
            with DatabaseLoader() as db_loader:
                dashboard_data = db_loader.export_to_json(self.output_file)
                
                logger.info(f"Dashboard data exported to: {self.output_file}")
                
                if self.verbose:
                    summary = dashboard_data.get('summary', {})
                    logger.info(f"Dashboard Summary: {summary}")
                
        except Exception as e:
            logger.error(f"Dashboard data export failed: {e}")
            raise
    
    def _finalize_run(self, success: bool = True, error: str = None) -> Dict[str, Any]:
        """Finalize the ETL run and return statistics"""
        self.stats['end_time'] = datetime.now().isoformat()
        self.stats['success'] = success
        
        if error:
            self.stats['error'] = error
        
        # Calculate duration
        if self.stats['start_time'] and self.stats['end_time']:
            start = datetime.fromisoformat(self.stats['start_time'])
            end = datetime.fromisoformat(self.stats['end_time'])
            duration = (end - start).total_seconds()
            self.stats['duration_seconds'] = duration
        
        # Log final statistics
        logger.info("="*50)
        logger.info("ETL PIPELINE SUMMARY")
        logger.info("="*50)
        logger.info(f"Run ID: {self.stats['run_id']}")
        logger.info(f"Success: {self.stats['success']}")
        logger.info(f"Duration: {self.stats.get('duration_seconds', 0):.2f} seconds")
        logger.info(f"XML Records Parsed: {self.stats['xml_parsed']}")
        logger.info(f"Records Cleaned: {self.stats['data_cleaned']}")
        logger.info(f"Records Categorized: {self.stats['data_categorized']}")
        logger.info(f"Records Loaded to DB: {self.stats['data_loaded']}")
        logger.info(f"Errors: {self.stats['errors']}")
        
        if error:
            logger.error(f"Error: {error}")
        
        logger.info("="*50)
        
        return self.stats

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='MoMo SMS Data ETL Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python etl/run.py --xml data/raw/momo.xml
  python etl/run.py --xml data/raw/momo.xml --output data/processed/custom_output.json
  python etl/run.py --verbose
        '''
    )
    
    parser.add_argument(
        '--xml',
        type=str,
        help='Path to input XML file (default: from config)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Path to output JSON file (default: from config)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    try:
        # Create and run ETL pipeline
        pipeline = ETLPipeline(
            xml_file=args.xml,
            output_file=args.output,
            verbose=args.verbose
        )
        
        results = pipeline.run()
        
        # Exit with appropriate code
        if results.get('success', False):
            logger.info("ETL pipeline completed successfully!")
            sys.exit(0)
        else:
            logger.error("ETL pipeline failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("ETL pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
