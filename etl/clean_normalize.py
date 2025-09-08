"""
Data cleaning and normalization module
Handles amounts, dates, phone number normalization
"""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dateutil import parser as date_parser

from .config import config

logger = logging.getLogger(__name__)

class DataCleaner:
    """Cleans and normalizes transaction data"""
    
    def __init__(self):
        self.cleaned_count = 0
        self.error_count = 0
        self.validation_errors = []
    
    def clean_transactions(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean and normalize a list of transactions"""
        cleaned_transactions = []
        
        for transaction in transactions:
            try:
                cleaned_transaction = self._clean_single_transaction(transaction)
                if cleaned_transaction:
                    cleaned_transactions.append(cleaned_transaction)
                    self.cleaned_count += 1
                else:
                    self.error_count += 1
            except Exception as e:
                logger.warning(f"Error cleaning transaction: {e}")
                self.error_count += 1
                continue
        
        logger.info(f"Cleaned {self.cleaned_count} transactions, {self.error_count} errors")
        return cleaned_transactions
    
    def _clean_single_transaction(self, transaction: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Clean and normalize a single transaction"""
        cleaned = transaction.copy()
        
        # Clean and normalize phone number
        phone = self._normalize_phone_number(
            transaction.get('phone') or 
            transaction.get('sender') or 
            transaction.get('recipient')
        )
        if not phone:
            self._add_validation_error(transaction, "No valid phone number found")
            return None
        cleaned['phone'] = phone
        
        # Clean and normalize date
        date = self._normalize_date(
            transaction.get('date') or 
            transaction.get('timestamp')
        )
        if not date:
            # Use current date if no date found
            date = datetime.now().isoformat()
            logger.warning("No date found, using current timestamp")
        cleaned['date'] = date
        
        # Clean and normalize amount
        amount = self._normalize_amount(transaction.get('amount'))
        if amount is None:
            self._add_validation_error(transaction, "No valid amount found")
            return None
        cleaned['amount'] = amount
        
        # Clean description
        cleaned['description'] = self._clean_text(transaction.get('description', ''))
        
        # Normalize status
        cleaned['status'] = self._normalize_status(transaction.get('status', 'unknown'))
        
        # Add cleaning metadata
        cleaned['cleaned_at'] = datetime.now().isoformat()
        
        # Validate the cleaned transaction
        if not self._validate_transaction(cleaned):
            return None
        
        return cleaned
    
    def _normalize_phone_number(self, phone: Optional[str]) -> Optional[str]:
        """Normalize phone number to standard format"""
        if not phone:
            return None
        
        # Remove all non-digit characters except +
        phone = re.sub(r'[^\d+]', '', str(phone))
        
        # Try to match against known patterns
        for pattern in config.PHONE_PATTERNS:
            if re.match(pattern, phone):
                # Convert to international format (+256XXXXXXXXX)
                if phone.startswith('+256'):
                    return phone
                elif phone.startswith('256'):
                    return '+' + phone
                elif phone.startswith('0') and len(phone) == 10:
                    return '+256' + phone[1:]
                elif len(phone) == 9:
                    return '+256' + phone
        
        # If no pattern matches, try to infer Uganda format
        if phone.isdigit():
            if len(phone) == 9:
                return '+256' + phone
            elif len(phone) == 10 and phone.startswith('0'):
                return '+256' + phone[1:]
        
        logger.warning(f"Could not normalize phone number: {phone}")
        return None
    
    def _normalize_date(self, date_str: Optional[str]) -> Optional[str]:
        """Normalize date to ISO format"""
        if not date_str:
            return None
        
        date_str = str(date_str).strip()
        
        # Try parsing with dateutil (flexible parser)
        try:
            parsed_date = date_parser.parse(date_str)
            return parsed_date.isoformat()
        except (ValueError, TypeError):
            pass
        
        # Try specific formats from config
        for date_format in config.DATE_FORMATS:
            try:
                parsed_date = datetime.strptime(date_str, date_format)
                return parsed_date.isoformat()
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def _normalize_amount(self, amount_str: Optional[str]) -> Optional[float]:
        """Normalize amount to float"""
        if not amount_str:
            return None
        
        amount_str = str(amount_str).strip()
        
        # Remove currency symbols and commas
        amount_str = re.sub(r'[^\d.-]', '', amount_str)
        
        try:
            amount = float(amount_str)
            
            # Validate amount range
            if amount < config.MIN_TRANSACTION_AMOUNT:
                logger.warning(f"Amount below minimum threshold: {amount}")
                return None
            
            if amount > config.MAX_TRANSACTION_AMOUNT:
                logger.warning(f"Amount above maximum threshold: {amount}")
                return None
            
            return round(amount, 2)
            
        except (ValueError, TypeError):
            logger.warning(f"Could not parse amount: {amount_str}")
            return None
    
    def _normalize_status(self, status: str) -> str:
        """Normalize transaction status"""
        if not status:
            return 'unknown'
        
        status = str(status).lower().strip()
        
        # Map various status representations to standard values
        status_mappings = {
            'success': ['success', 'successful', 'completed', 'done', 'ok', '1', 'true'],
            'failed': ['failed', 'failure', 'error', 'rejected', 'declined', '0', 'false'],
            'pending': ['pending', 'processing', 'in_progress', 'waiting']
        }
        
        for standard_status, variants in status_mappings.items():
            if status in variants:
                return standard_status
        
        return 'unknown'
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text fields"""
        if not text:
            return ''
        
        text = str(text).strip()
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might cause issues
        text = re.sub(r'[^\w\s\-.,!?()]', '', text)
        
        return text
    
    def _validate_transaction(self, transaction: Dict[str, Any]) -> bool:
        """Validate cleaned transaction meets requirements"""
        required_fields = ['phone', 'amount', 'date']
        
        for field in required_fields:
            if field not in transaction or not transaction[field]:
                self._add_validation_error(transaction, f"Missing required field: {field}")
                return False
        
        # Additional validations
        if not isinstance(transaction['amount'], (int, float)) or transaction['amount'] <= 0:
            self._add_validation_error(transaction, "Invalid amount")
            return False
        
        if not transaction['phone'].startswith('+'):
            self._add_validation_error(transaction, "Invalid phone format")
            return False
        
        return True
    
    def _add_validation_error(self, transaction: Dict[str, Any], error: str):
        """Add validation error to error list"""
        self.validation_errors.append({
            'transaction_id': transaction.get('id', 'unknown'),
            'error': error,
            'transaction_data': transaction
        })
        logger.warning(f"Validation error: {error}")
    
    def get_cleaning_stats(self) -> Dict[str, Any]:
        """Get cleaning statistics"""
        total_processed = self.cleaned_count + self.error_count
        success_rate = self.cleaned_count / total_processed if total_processed > 0 else 0
        
        return {
            'total_processed': total_processed,
            'successfully_cleaned': self.cleaned_count,
            'errors': self.error_count,
            'success_rate': success_rate,
            'validation_errors': len(self.validation_errors)
        }
    
    def export_validation_errors(self, filepath: str = None):
        """Export validation errors to file for review"""
        if not self.validation_errors:
            return
        
        if not filepath:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = config.get_absolute_path(f"data/logs/validation_errors_{timestamp}.json")
        
        try:
            import json
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.validation_errors, f, indent=2, default=str)
            
            logger.info(f"Exported {len(self.validation_errors)} validation errors to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export validation errors: {e}")

# Convenience function
def clean_transaction_data(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Quick function to clean transaction data"""
    cleaner = DataCleaner()
    return cleaner.clean_transactions(transactions)
