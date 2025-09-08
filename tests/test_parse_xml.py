"""
Unit tests for XML parsing module
"""

import pytest
import xml.etree.ElementTree as ET
from pathlib import Path
import tempfile
import os

from etl.parse_xml import XMLParser, parse_xml_file


class TestXMLParser:
    """Test cases for XMLParser class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = XMLParser()
        
    def create_test_xml(self, content: str) -> str:
        """Create a temporary XML file for testing"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False)
        temp_file.write(content)
        temp_file.close()
        return temp_file.name
        
    def teardown_method(self):
        """Clean up after tests"""
        # Remove any temporary files created during tests
        pass
    
    def test_parse_simple_xml(self):
        """Test parsing a simple XML structure"""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <transactions>
            <transaction>
                <id>1</id>
                <phone>+256701234567</phone>
                <amount>1000.50</amount>
                <date>2023-01-01 12:00:00</date>
                <description>Test transaction</description>
            </transaction>
        </transactions>'''
        
        xml_file = self.create_test_xml(xml_content)
        
        try:
            parser = XMLParser(xml_file)
            transactions = parser.parse_file()
            
            assert len(transactions) == 1
            assert transactions[0]['id'] == '1'
            assert transactions[0]['phone'] == '+256701234567'
            assert transactions[0]['amount'] == '1000.50'
            assert transactions[0]['description'] == 'Test transaction'
            
        finally:
            os.unlink(xml_file)
    
    def test_parse_multiple_transactions(self):
        """Test parsing multiple transactions"""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <root>
            <transaction id="1" phone="+256701111111" amount="500">
                <date>2023-01-01</date>
            </transaction>
            <transaction id="2" phone="+256702222222" amount="750">
                <date>2023-01-02</date>
            </transaction>
        </root>'''
        
        xml_file = self.create_test_xml(xml_content)
        
        try:
            parser = XMLParser(xml_file)
            transactions = parser.parse_file()
            
            assert len(transactions) == 2
            assert transactions[0]['id'] == '1'
            assert transactions[1]['id'] == '2'
            
        finally:
            os.unlink(xml_file)
    
    def test_parse_nonexistent_file(self):
        """Test parsing a non-existent file"""
        parser = XMLParser("nonexistent_file.xml")
        transactions = parser.parse_file()
        
        assert transactions == []
    
    def test_parse_invalid_xml(self):
        """Test parsing invalid XML"""
        invalid_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <transactions>
            <transaction>
                <id>1</id>
                <phone>+256701234567</phone>
                <unclosed_tag>
            </transaction>
        </transactions>'''
        
        xml_file = self.create_test_xml(invalid_xml)
        
        try:
            parser = XMLParser(xml_file)
            transactions = parser.parse_file()
            
            # Should return empty list for invalid XML
            assert transactions == []
            
        finally:
            os.unlink(xml_file)
    
    def test_validate_xml_structure(self):
        """Test XML structure validation"""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <transactions>
            <transaction>
                <id>1</id>
            </transaction>
        </transactions>'''
        
        xml_file = self.create_test_xml(xml_content)
        
        try:
            parser = XMLParser(xml_file)
            assert parser.validate_xml_structure() == True
            
        finally:
            os.unlink(xml_file)
    
    def test_extract_field_value(self):
        """Test field value extraction"""
        xml_string = '''<transaction id="123" amount="500.00">
            <phone>+256701234567</phone>
            <description>Test transaction</description>
        </transaction>'''
        
        element = ET.fromstring(xml_string)
        parser = XMLParser()
        
        # Test attribute extraction
        id_value = parser._extract_field_value(element, ['id'])
        assert id_value == '123'
        
        # Test child element extraction
        phone_value = parser._extract_field_value(element, ['phone'])
        assert phone_value == '+256701234567'
        
        # Test non-existent field
        missing_value = parser._extract_field_value(element, ['nonexistent'])
        assert missing_value is None


def test_parse_xml_file_convenience_function():
    """Test the convenience function for parsing XML files"""
    # This would typically use a mock or test file
    # For now, just test that it returns a list
    transactions = parse_xml_file("nonexistent.xml")
    assert isinstance(transactions, list)


if __name__ == "__main__":
    pytest.main([__file__])
