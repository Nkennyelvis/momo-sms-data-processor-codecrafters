"""
Transaction categorization module
Simple rules for transaction types based on descriptions and patterns
"""

import re
import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict

from .config import config

logger = logging.getLogger(__name__)

class TransactionCategorizer:
    """Categorizes transactions based on rules and patterns"""
    
    def __init__(self):
        self.category_stats = defaultdict(int)
        self.uncategorized_count = 0
        
    def categorize_transactions(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Categorize a list of transactions"""
        categorized_transactions = []
        
        for transaction in transactions:
            try:
                categorized_transaction = self._categorize_single_transaction(transaction)
                categorized_transactions.append(categorized_transaction)
                
                # Track statistics
                category = categorized_transaction.get('category', 'other')
                self.category_stats[category] += 1
                
            except Exception as e:
                logger.warning(f"Error categorizing transaction: {e}")
                # Add default category if categorization fails
                transaction['category'] = 'other'
                categorized_transactions.append(transaction)
                self.category_stats['other'] += 1
        
        logger.info(f"Categorized {len(categorized_transactions)} transactions")
        self._log_category_stats()
        
        return categorized_transactions
    
    def _categorize_single_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Categorize a single transaction"""
        categorized = transaction.copy()
        
        # Get text to analyze (description, sender, recipient info)
        text_to_analyze = self._get_categorization_text(transaction)
        
        # Try to categorize based on keywords
        category = self._categorize_by_keywords(text_to_analyze)
        
        # If no keyword match, try amount-based categorization
        if category == 'other':
            category = self._categorize_by_amount(transaction.get('amount', 0))
        
        # If still no match, try pattern-based categorization
        if category == 'other':
            category = self._categorize_by_patterns(text_to_analyze)
        
        categorized['category'] = category
        categorized['categorized_at'] = transaction.get('cleaned_at', '')
        
        return categorized
    
    def _get_categorization_text(self, transaction: Dict[str, Any]) -> str:
        """Extract relevant text for categorization analysis"""
        text_parts = []
        
        # Add description
        if 'description' in transaction and transaction['description']:
            text_parts.append(str(transaction['description']))
        
        # Add any other relevant text fields
        for field in ['message', 'text', 'note', 'reference']:
            if field in transaction and transaction[field]:
                text_parts.append(str(transaction[field]))
        
        return ' '.join(text_parts).lower().strip()
    
    def _categorize_by_keywords(self, text: str) -> str:
        """Categorize based on keyword matching"""
        if not text:
            return 'other'
        
        # Score each category based on keyword matches
        category_scores = defaultdict(int)
        
        for category, keywords in config.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                matches = len(re.findall(pattern, text))
                category_scores[category] += matches
        
        # Return category with highest score
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            if category_scores[best_category] > 0:
                return best_category
        
        return 'other'
    
    def _categorize_by_amount(self, amount: float) -> str:
        """Categorize based on amount patterns"""
        if not amount or amount <= 0:
            return 'other'
        
        # Define amount-based rules (these are examples, adjust as needed)
        if amount < 500:  # Small amounts often airtime
            return 'airtime'
        elif amount >= 10000:  # Large amounts often transfers
            return 'transfer'
        elif 1000 <= amount < 5000:  # Medium amounts often payments
            return 'payment'
        
        return 'other'
    
    def _categorize_by_patterns(self, text: str) -> str:
        """Categorize based on text patterns"""
        if not text:
            return 'other'
        
        # Define regex patterns for different categories
        patterns = {
            'airtime': [
                r'\d+mb',  # Data bundles
                r'bundle',
                r'min(ute)?s?\s*\d+',  # Minutes
                r'recharge',
                r'top\s*up'
            ],
            'transfer': [
                r'send\s+money',
                r'transfer\s+to',
                r'sent\s+\$?\d+',
                r'received\s+from'
            ],
            'payment': [
                r'pay\s+for',
                r'purchase',
                r'bought?',
                r'merchant',
                r'shop'
            ],
            'deposit': [
                r'deposit',
                r'add\s+money',
                r'cash\s+in',
                r'load'
            ],
            'withdrawal': [
                r'withdraw',
                r'cash\s+out',
                r'atm'
            ]
        }
        
        # Check patterns for each category
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, text, re.IGNORECASE):
                    return category
        
        return 'other'
    
    def _log_category_stats(self):
        """Log categorization statistics"""
        total = sum(self.category_stats.values())
        if total == 0:
            return
        
        logger.info("Category distribution:")
        for category, count in sorted(self.category_stats.items()):
            percentage = (count / total) * 100
            logger.info(f"  {category}: {count} ({percentage:.1f}%)")
    
    def get_category_stats(self) -> Dict[str, Any]:
        """Get categorization statistics"""
        total = sum(self.category_stats.values())
        
        stats = {
            'total_categorized': total,
            'category_distribution': dict(self.category_stats)
        }
        
        if total > 0:
            stats['category_percentages'] = {
                category: (count / total) * 100 
                for category, count in self.category_stats.items()
            }
        
        return stats
    
    def suggest_new_keywords(self, transactions: List[Dict[str, Any]], category: str = None) -> List[str]:
        """Analyze uncategorized transactions to suggest new keywords"""
        if category:
            # Analyze transactions of specific category
            target_transactions = [
                t for t in transactions 
                if t.get('category') == category
            ]
        else:
            # Analyze uncategorized transactions
            target_transactions = [
                t for t in transactions 
                if t.get('category') == 'other'
            ]
        
        if not target_transactions:
            return []
        
        # Extract common words from descriptions
        word_counts = defaultdict(int)
        
        for transaction in target_transactions:
            text = self._get_categorization_text(transaction)
            words = re.findall(r'\b\w{3,}\b', text.lower())
            
            for word in words:
                # Skip common words
                if word not in ['the', 'and', 'for', 'you', 'your', 'from', 'with']:
                    word_counts[word] += 1
        
        # Return most common words as keyword suggestions
        suggested_keywords = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        return [word for word, count in suggested_keywords if count > 1]
    
    def update_category_rules(self, new_keywords: Dict[str, List[str]]):
        """Update category keywords with new rules"""
        for category, keywords in new_keywords.items():
            if category in config.CATEGORY_KEYWORDS:
                config.CATEGORY_KEYWORDS[category].extend(keywords)
            else:
                config.CATEGORY_KEYWORDS[category] = keywords
        
        logger.info(f"Updated category rules with {len(new_keywords)} new keyword sets")

# Convenience function
def categorize_transaction_data(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Quick function to categorize transaction data"""
    categorizer = TransactionCategorizer()
    return categorizer.categorize_transactions(transactions)
