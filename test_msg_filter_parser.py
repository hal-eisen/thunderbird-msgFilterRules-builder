import unittest
from unittest.mock import patch, mock_open
import tempfile
import os
from datetime import datetime

# We'll implement this module
from msg_filter_parser import MsgFilterParser, MsgFilterRule


class TestMsgFilterParser(unittest.TestCase):
    """Test cases for parsing Thunderbird message filter rules."""
    
    def setUp(self):
        self.parser = MsgFilterParser()
    
    def test_parse_empty_file(self):
        """Test parsing an empty file."""
        content = ""
        with patch('builtins.open', mock_open(read_data=content)):
            rules = self.parser.parse_file("dummy_path")
            self.assertEqual(len(rules), 0)
    
    def test_parse_file_with_version_only(self):
        """Test parsing a file with only version and logging."""
        content = '''version="9"
logging="no"'''
        with patch('builtins.open', mock_open(read_data=content)):
            rules = self.parser.parse_file("dummy_path")
            self.assertEqual(len(rules), 0)
            self.assertEqual(self.parser.version, "9")
            self.assertEqual(self.parser.logging, "no")
    
    def test_parse_single_rule(self):
        """Test parsing a single rule."""
        content = '''version="9"
logging="no"
name="Example Filter Name"
enabled="yes"
type="17"
action="Move to folder"
actionValue="imap://user%40host.com@imap.server.com/Promotions"
condition="AND (from,contains,newsletter@example.com)"'''
        
        with patch('builtins.open', mock_open(read_data=content)):
            rules = self.parser.parse_file("dummy_path")
            self.assertEqual(len(rules), 1)
            
            rule = rules[0]
            self.assertEqual(rule.name, "Example Filter Name")
            self.assertEqual(rule.enabled, "yes")
            self.assertEqual(rule.type, "17")
            self.assertEqual(rule.action, "Move to folder")
            self.assertEqual(rule.action_value, "imap://user%40host.com@imap.server.com/Promotions")
            self.assertEqual(rule.condition, "AND (from,contains,newsletter@example.com)")
    
    def test_parse_multiple_rules(self):
        """Test parsing multiple rules."""
        content = '''version="9"
logging="no"
name="First Rule"
enabled="yes"
type="17"
action="Move to folder"
actionValue="imap://user@host.com/Folder1"
condition="AND (from,contains,test1@example.com)"
name="Second Rule"
enabled="no"
type="17"
action="Copy to folder"
actionValue="imap://user@host.com/Folder2"
condition="AND (subject,contains,Important)"'''
        
        with patch('builtins.open', mock_open(read_data=content)):
            rules = self.parser.parse_file("dummy_path")
            self.assertEqual(len(rules), 2)
            
            self.assertEqual(rules[0].name, "First Rule")
            self.assertEqual(rules[0].enabled, "yes")
            self.assertEqual(rules[0].action, "Move to folder")
            
            self.assertEqual(rules[1].name, "Second Rule")
            self.assertEqual(rules[1].enabled, "no")
            self.assertEqual(rules[1].action, "Copy to folder")
    
    def test_parse_condition_with_multiple_terms(self):
        """Test parsing a condition with multiple terms."""
        content = '''version="9"
logging="no"
name="Multi-term Rule"
enabled="yes"
type="17"
action="Move to folder"
actionValue="imap://user@host.com/Folder"
condition="AND (from,contains,test@example.com) (subject,contains,urgent)"'''
        
        with patch('builtins.open', mock_open(read_data=content)):
            rules = self.parser.parse_file("dummy_path")
            self.assertEqual(len(rules), 1)
            
            rule = rules[0]
            self.assertEqual(rule.condition, "AND (from,contains,test@example.com) (subject,contains,urgent)")


class TestMsgFilterRule(unittest.TestCase):
    """Test cases for individual message filter rules."""
    
    def test_rule_creation(self):
        """Test creating a rule with basic properties."""
        rule = MsgFilterRule(
            name="Test Rule",
            enabled="yes",
            type="17",
            action="Move to folder",
            action_value="imap://user@host.com/Folder",
            condition="AND (from,contains,test@example.com)"
        )
        
        self.assertEqual(rule.name, "Test Rule")
        self.assertEqual(rule.enabled, "yes")
        self.assertEqual(rule.type, "17")
        self.assertEqual(rule.action, "Move to folder")
        self.assertEqual(rule.action_value, "imap://user@host.com/Folder")
        self.assertEqual(rule.condition, "AND (from,contains,test@example.com)")
    
    def test_rule_to_string(self):
        """Test converting a rule back to string format."""
        rule = MsgFilterRule(
            name="Test Rule",
            enabled="yes",
            type="17",
            action="Move to folder",
            action_value="imap://user@host.com/Folder",
            condition="AND (from,contains,test@example.com)"
        )
        
        expected = '''name="Test Rule"
enabled="yes"
type="17"
action="Move to folder"
actionValue="imap://user@host.com/Folder"
condition="AND (from,contains,test@example.com)"'''
        
        self.assertEqual(rule.to_string(), expected)


if __name__ == '__main__':
    unittest.main()
