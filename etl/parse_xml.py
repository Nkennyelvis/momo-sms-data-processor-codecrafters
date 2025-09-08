"""
XML parsing module for MoMo SMS data
Handles parsing of XML files using ElementTree/lxml
"""

import xml.etree.ElementTree as ET
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime

from .config import config

logger = logging.getLogger(__name__)

class XMLParser:
    """Parser for MoMo SMS XML data"""
    
    def __init__(self, xml_file_path: str = None):
        self.xml_file_path = xml_file_path or config.XML_INPUT_PATH
        self.parsed_data = []
        self.errors = []
        
    def parse_file(self) -> List[Dict[str, Any]]:
        """Parse XML file and return list of transaction dictionaries"""
        try:
            xml_path = config.get_absolute_path(self.xml_file_path)
            
            if not xml_path.exists():
                logger.error(f"XML file not found: {xml_path}")
                return []
            
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            logger.info(f"Parsing XML file: {xml_path}")
            logger.info(f"Root element: {root.tag}")
            
            # Parse based on common SMS XML structures
            transactions = self._parse_transactions(root)
            
            logger.info(f"Successfully parsed {len(transactions)} transactions")
            return transactions
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            self._save_to_dead_letter(f"XML Parse Error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing XML: {e}")
            return []
    
    def _parse_transactions(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract transaction data from XML root element"""
        transactions = []
        
        # Try different common XML structures
        transaction_elements = (
            root.findall('.//transaction') or
            root.findall('.//sms') or
            root.findall('.//message') or
            root.findall('.//record') or
            [root]  # Single transaction in root
        )
        
        for element in transaction_elements:
            try:
                transaction = self._parse_single_transaction(element)
                if transaction:
                    transactions.append(transaction)
            except Exception as e:
                logger.warning(f"Error parsing transaction element: {e}")
                self._save_to_dead_letter(ET.tostring(element, encoding='unicode'))
                continue
        
        return transactions
    
    def _parse_single_transaction(self, element: ET.Element) -> Optional[Dict[str, Any]]:
        """Parse a single transaction element"""
        transaction = {}
        
        # Try to extract common fields
        field_mappings = {
            'id': ['id', 'transaction_id', 'ref', 'reference'],
            'date': ['date', 'timestamp', 'time', 'datetime'],
            'phone': ['phone', 'number', 'mobile', 'msisdn'],
            'amount': ['amount', 'value', 'sum', 'total'],
            'description': ['description', 'desc', 'message', 'text'],
            'sender': ['sender', 'from', 'source'],
            'recipient': ['recipient', 'to', 'destination'],
            'status': ['status', 'state', 'result']
        }
        
        # Extract fields from attributes and child elements
        for field, possible_names in field_mappings.items():
            value = self._extract_field_value(element, possible_names)
            if value:
                transaction[field] = value
        
        # Ensure we have minimum required fields
        if not any(key in transaction for key in ['phone', 'sender', 'recipient']):
            return None
        
        # Add parsing metadata
        transaction['parsed_at'] = datetime.now().isoformat()
        transaction['raw_xml'] = ET.tostring(element, encoding='unicode')[:500]  # Truncate for storage
        
        return transaction
    
    def _extract_field_value(self, element: ET.Element, field_names: List[str]) -> Optional[str]:
        """Extract field value from element attributes or child elements"""
        # Check attributes first
        for name in field_names:
            if name in element.attrib:
                return element.attrib[name].strip()
        
        # Check child elements
        for name in field_names:
            child = element.find(name)
            if child is not None and child.text:
                return child.text.strip()
        
        # Check case-insensitive
        for name in field_names:
            for child in element:
                if child.tag.lower() == name.lower() and child.text:
                    return child.text.strip()
        
        return None
    
    def _save_to_dead_letter(self, content: str):
        """Save unparseable content to dead letter queue"""
        try:
            dead_letter_dir = config.get_absolute_path(config.DEAD_LETTER_PATH)
            dead_letter_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"unparsed_{timestamp}.xml"
            filepath = dead_letter_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.warning(f"Saved unparseable content to: {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save to dead letter queue: {e}")
    
    def validate_xml_structure(self) -> bool:
        """Validate XML file structure before parsing"""
        try:
            xml_path = config.get_absolute_path(self.xml_file_path)
            
            if not xml_path.exists():
                logger.error(f"XML file not found: {xml_path}")
                return False
            
            # Quick validation - try to parse without processing
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            logger.info(f"XML validation successful. Root: {root.tag}")
            return True
            
        except ET.ParseError as e:
            logger.error(f"XML validation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"XML validation error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get parsing statistics"""
        return {
            'file_path': self.xml_file_path,
            'total_parsed': len(self.parsed_data),
            'total_errors': len(self.errors),
            'success_rate': len(self.parsed_data) / (len(self.parsed_data) + len(self.errors)) if (self.parsed_data or self.errors) else 0
        }

# Convenience function for quick parsing
def parse_xml_file(xml_file_path: str = None) -> List[Dict[str, Any]]:
    """Quick function to parse XML file and return transactions"""
    parser = XMLParser(xml_file_path)
    return parser.parse_file()
