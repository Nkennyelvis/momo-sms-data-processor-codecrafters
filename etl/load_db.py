"""
Database loading module for MoMo SMS data
Handles SQLite database creation, table schemas, and data loading
"""

import sqlite3
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime

from .config import config

logger = logging.getLogger(__name__)

class DatabaseLoader:
    """Handles loading processed transaction data into SQLite database"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.get_absolute_path(config.DATABASE_PATH)
        self.connection = None
        self.loaded_count = 0
        self.error_count = 0
        
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
    
    def connect(self):
        """Establish database connection"""
        try:
            # Ensure the database directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row  # Enable dict-like access
            
            logger.info(f"Connected to database: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Database connection closed")
    
    def create_tables(self):
        """Create database tables if they don't exist"""
        try:
            cursor = self.connection.cursor()
            
            # Main transactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id TEXT PRIMARY KEY,
                    date TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT,
                    status TEXT,
                    description TEXT,
                    sender TEXT,
                    recipient TEXT,
                    parsed_at TEXT,
                    cleaned_at TEXT,
                    categorized_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ETL processing log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS etl_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT UNIQUE NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    status TEXT NOT NULL,
                    records_processed INTEGER DEFAULT 0,
                    records_loaded INTEGER DEFAULT 0,
                    records_failed INTEGER DEFAULT 0,
                    source_file TEXT,
                    error_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Data quality metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_quality_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    metric_type TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES etl_runs (run_id)
                )
            ''')
            
            # Transaction categories lookup table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    keywords TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_phone ON transactions(phone)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_etl_runs_run_id ON etl_runs(run_id)')
            
            self.connection.commit()
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def load_transactions(self, transactions: List[Dict[str, Any]], run_id: str = None) -> Dict[str, Any]:
        """Load transactions into database"""
        if not transactions:
            logger.warning("No transactions to load")
            return {"loaded": 0, "failed": 0, "skipped": 0}
        
        run_id = run_id or f"etl_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        loaded_count = 0
        failed_count = 0
        skipped_count = 0
        
        try:
            cursor = self.connection.cursor()
            
            for transaction in transactions:
                try:
                    # Prepare transaction data
                    tx_data = self._prepare_transaction_data(transaction)
                    
                    # Check if transaction already exists
                    if self._transaction_exists(tx_data.get('id')):
                        # Update existing transaction
                        if self._update_transaction(tx_data):
                            loaded_count += 1
                        else:
                            skipped_count += 1
                    else:
                        # Insert new transaction
                        if self._insert_transaction(tx_data):
                            loaded_count += 1
                        else:
                            failed_count += 1
                            
                except Exception as e:
                    logger.warning(f"Failed to load transaction {transaction.get('id', 'unknown')}: {e}")
                    failed_count += 1
                    continue
            
            self.connection.commit()
            
            # Log the results
            logger.info(f"Loaded {loaded_count} transactions, {failed_count} failed, {skipped_count} skipped")
            
            # Update ETL run log
            self._update_etl_run_log(run_id, loaded_count, failed_count)
            
            return {
                "loaded": loaded_count,
                "failed": failed_count,
                "skipped": skipped_count,
                "run_id": run_id
            }
            
        except Exception as e:
            logger.error(f"Database loading failed: {e}")
            self.connection.rollback()
            raise
    
    def _prepare_transaction_data(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare transaction data for database insertion"""
        # Ensure required fields have default values
        tx_data = {
            'id': transaction.get('id') or f"tx_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(str(transaction)) % 10000}",
            'date': transaction.get('date'),
            'phone': transaction.get('phone'),
            'amount': float(transaction.get('amount', 0)),
            'category': transaction.get('category', 'other'),
            'status': transaction.get('status', 'unknown'),
            'description': transaction.get('description', ''),
            'sender': transaction.get('sender'),
            'recipient': transaction.get('recipient'),
            'parsed_at': transaction.get('parsed_at'),
            'cleaned_at': transaction.get('cleaned_at'),
            'categorized_at': transaction.get('categorized_at')
        }
        
        return tx_data
    
    def _transaction_exists(self, transaction_id: str) -> bool:
        """Check if transaction already exists in database"""
        cursor = self.connection.cursor()
        cursor.execute('SELECT 1 FROM transactions WHERE id = ?', (transaction_id,))
        return cursor.fetchone() is not None
    
    def _insert_transaction(self, tx_data: Dict[str, Any]) -> bool:
        """Insert new transaction into database"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO transactions (
                    id, date, phone, amount, category, status, description,
                    sender, recipient, parsed_at, cleaned_at, categorized_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tx_data['id'], tx_data['date'], tx_data['phone'], tx_data['amount'],
                tx_data['category'], tx_data['status'], tx_data['description'],
                tx_data['sender'], tx_data['recipient'], tx_data['parsed_at'],
                tx_data['cleaned_at'], tx_data['categorized_at']
            ))
            return True
            
        except Exception as e:
            logger.warning(f"Failed to insert transaction {tx_data['id']}: {e}")
            return False
    
    def _update_transaction(self, tx_data: Dict[str, Any]) -> bool:
        """Update existing transaction in database"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                UPDATE transactions SET
                    date = ?, phone = ?, amount = ?, category = ?, status = ?,
                    description = ?, sender = ?, recipient = ?, parsed_at = ?,
                    cleaned_at = ?, categorized_at = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                tx_data['date'], tx_data['phone'], tx_data['amount'],
                tx_data['category'], tx_data['status'], tx_data['description'],
                tx_data['sender'], tx_data['recipient'], tx_data['parsed_at'],
                tx_data['cleaned_at'], tx_data['categorized_at'], tx_data['id']
            ))
            return True
            
        except Exception as e:
            logger.warning(f"Failed to update transaction {tx_data['id']}: {e}")
            return False
    
    def _update_etl_run_log(self, run_id: str, loaded: int, failed: int):
        """Update ETL run log with results"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                UPDATE etl_runs SET
                    end_time = ?, status = ?, records_loaded = ?, records_failed = ?
                WHERE run_id = ?
            ''', (
                datetime.now().isoformat(), 'completed', loaded, failed, run_id
            ))
            self.connection.commit()
            
        except Exception as e:
            logger.warning(f"Failed to update ETL run log: {e}")
    
    def create_etl_run_log(self, run_id: str, source_file: str = None) -> str:
        """Create new ETL run log entry"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO etl_runs (run_id, start_time, status, source_file)
                VALUES (?, ?, ?, ?)
            ''', (run_id, datetime.now().isoformat(), 'running', source_file))
            
            self.connection.commit()
            logger.info(f"Created ETL run log: {run_id}")
            return run_id
            
        except Exception as e:
            logger.error(f"Failed to create ETL run log: {e}")
            raise
    
    def get_transactions(self, limit: int = None, category: str = None, 
                        status: str = None) -> List[Dict[str, Any]]:
        """Retrieve transactions from database"""
        try:
            cursor = self.connection.cursor()
            
            query = 'SELECT * FROM transactions WHERE 1=1'
            params = []
            
            if category:
                query += ' AND category = ?'
                params.append(category)
            
            if status:
                query += ' AND status = ?'
                params.append(status)
            
            query += ' ORDER BY date DESC'
            
            if limit:
                query += ' LIMIT ?'
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to retrieve transactions: {e}")
            return []
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics from database"""
        try:
            cursor = self.connection.cursor()
            
            # Basic counts
            cursor.execute('SELECT COUNT(*) as total_transactions FROM transactions')
            total_transactions = cursor.fetchone()['total_transactions']
            
            cursor.execute('SELECT SUM(amount) as total_volume FROM transactions')
            total_volume = cursor.fetchone()['total_volume'] or 0
            
            cursor.execute('SELECT AVG(amount) as avg_transaction FROM transactions')
            avg_transaction = cursor.fetchone()['avg_transaction'] or 0
            
            cursor.execute('SELECT COUNT(DISTINCT phone) as active_users FROM transactions')
            active_users = cursor.fetchone()['active_users']
            
            # Category distribution
            cursor.execute('''
                SELECT category, COUNT(*) as count 
                FROM transactions 
                GROUP BY category 
                ORDER BY count DESC
            ''')
            category_distribution = {row['category']: row['count'] for row in cursor.fetchall()}
            
            # Status distribution
            cursor.execute('''
                SELECT status, COUNT(*) as count 
                FROM transactions 
                GROUP BY status
            ''')
            status_distribution = {row['status']: row['count'] for row in cursor.fetchall()}
            
            return {
                'total_transactions': total_transactions,
                'total_volume': round(total_volume, 2),
                'average_transaction': round(avg_transaction, 2),
                'active_users': active_users,
                'category_distribution': category_distribution,
                'status_distribution': status_distribution,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get summary stats: {e}")
            return {}
    
    def export_to_json(self, output_path: str = None) -> Dict[str, Any]:
        """Export database data to JSON for dashboard"""
        try:
            if output_path:
                output_path = Path(output_path)
            else:
                output_path = config.get_absolute_path(config.JSON_OUTPUT_PATH)
            
            # Get summary statistics
            summary = self.get_summary_stats()
            
            # Get recent transactions (limit to avoid memory issues)
            transactions = self.get_transactions(limit=1000)
            
            # Prepare dashboard data
            dashboard_data = {
                'summary': {
                    'totalTransactions': summary.get('total_transactions', 0),
                    'totalVolume': summary.get('total_volume', 0),
                    'averageTransaction': summary.get('average_transaction', 0),
                    'activeUsers': summary.get('active_users', 0)
                },
                'transactions': transactions,
                'categories': list(summary.get('category_distribution', {}).keys()),
                'categoryDistribution': summary.get('category_distribution', {}),
                'statusDistribution': summary.get('status_distribution', {}),
                'lastUpdated': summary.get('last_updated')
            }
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(dashboard_data, f, indent=2, default=str)
            
            logger.info(f"Dashboard data exported to: {output_path}")
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Failed to export dashboard data: {e}")
            raise

# Convenience functions
def load_transactions_to_db(transactions: List[Dict[str, Any]], db_path: str = None) -> Dict[str, Any]:
    """Quick function to load transactions to database"""
    with DatabaseLoader(db_path) as loader:
        loader.create_tables()
        return loader.load_transactions(transactions)

def export_dashboard_data(db_path: str = None, output_path: str = None) -> Dict[str, Any]:
    """Quick function to export dashboard data"""
    with DatabaseLoader(db_path) as loader:
        return loader.export_to_json(output_path)
