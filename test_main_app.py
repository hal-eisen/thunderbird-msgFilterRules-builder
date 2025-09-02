import unittest
from unittest.mock import patch, mock_open, MagicMock
import tempfile
import os
from datetime import datetime
import shutil

from msg_filter_parser import MsgFilterParser, MsgFilterRule
from main import FilterAdderApp


class TestFilterAdderApp(unittest.TestCase):
    """Test cases for the main filter adder application."""
    
    def setUp(self):
        self.app = FilterAdderApp()
        self.test_file_path = "/home/USER/snap/thunderbird/common/.thunderbird/PROFILE.default/ImapMail/imap.EXAMPLE.COM/msgFilterRules.dat"
    
    def test_validate_header_field_valid(self):
        """Test validation of valid header fields."""
        valid_fields = ["from", "to", "cc", "subject"]
        for field in valid_fields:
            self.assertTrue(self.app.validate_header_field(field))
    
    def test_validate_header_field_invalid(self):
        """Test validation of invalid header fields."""
        invalid_fields = ["body", "date", "invalid"]
        for field in invalid_fields:
            self.assertFalse(self.app.validate_header_field(field))
    
    def test_create_backup_path(self):
        """Test creating backup file path with timestamp."""
        backup_path = self.app.create_backup_path(self.test_file_path)
        
        # Should be in same directory
        self.assertEqual(os.path.dirname(backup_path), os.path.dirname(self.test_file_path))
        
        # Should start with original filename
        base_name = os.path.basename(self.test_file_path)
        self.assertTrue(backup_path.startswith(os.path.join(os.path.dirname(self.test_file_path), base_name)))
        
        # Should contain timestamp and backup
        self.assertIn("backup", backup_path)
    
    @patch('shutil.copy2')
    def test_backup_file(self, mock_copy):
        """Test backing up the filter rules file."""
        self.app.backup_file(self.test_file_path)
        mock_copy.assert_called_once()
    
    def test_add_condition_to_existing_rule(self):
        """Test adding a condition to an existing rule."""
        # Create a parser with an existing rule
        parser = MsgFilterParser()
        parser.version = "9"
        parser.logging = "no"
        
        existing_rule = MsgFilterRule(
            name="Test Rule",
            enabled="yes",
            type="17",
            action="Move to folder",
            action_value="imap://user@host.com/Folder",
            condition="OR (from,contains,existing@example.com)"
        )
        parser.rules = [existing_rule]
        
        # Add a new condition
        success = parser.add_condition_to_rule("Test Rule", "subject", "urgent")
        
        self.assertTrue(success)
        self.assertEqual(
            parser.rules[0].condition,
            "OR (from,contains,existing@example.com) OR (subject,contains,urgent)"
        )
    
    def test_create_new_rule(self):
        """Test creating a new rule when it doesn't exist."""
        parser = MsgFilterParser()
        parser.version = "9"
        parser.logging = "no"
        
        new_rule = parser.create_new_rule(
            name="New Rule",
            header_field="from",
            value="new@example.com",
            action_value="imap://user@host.com/NewFolder"
        )
        
        self.assertEqual(len(parser.rules), 1)
        self.assertEqual(new_rule.name, "New Rule")
        self.assertEqual(new_rule.action, "Move to folder")
        self.assertEqual(new_rule.condition, "OR (from,contains,new@example.com)")
        self.assertEqual(new_rule.action_value, "imap://user@host.com/NewFolder")
    
    def test_find_rule_by_name(self):
        """Test finding a rule by name."""
        parser = MsgFilterParser()
        rule1 = MsgFilterRule(name="Rule 1")
        rule2 = MsgFilterRule(name="Rule 2")
        parser.rules = [rule1, rule2]
        
        found_rule = parser.find_rule_by_name("Rule 1")
        self.assertEqual(found_rule, rule1)
        
        not_found = parser.find_rule_by_name("Nonexistent")
        self.assertIsNone(not_found)
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists', return_value=True)
    def test_process_filter_rules_existing_rule(self, mock_exists, mock_file):
        """Test processing when the rule already exists."""
        # Mock file content with existing rule
        content = '''version="9"
logging="no"
name="Test Rule"
enabled="yes"
type="17"
action="Move to folder"
actionValue="imap://user@host.com/Folder"
condition="OR (from,contains,existing@example.com)"'''
        
        mock_file.return_value.read.return_value = content
        
        with patch('shutil.copy2') as mock_backup:
            success = self.app.process_filter_rules(
                rule_name="Test Rule",
                header_field="subject",
                value="urgent",
                dest_folder="imap://user@host.com/Folder"
            )
        
        self.assertTrue(success)
        mock_backup.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists', return_value=True)
    def test_process_filter_rules_new_rule(self, mock_exists, mock_file):
        """Test processing when creating a new rule."""
        # Mock empty file content
        content = '''version="9"
logging="no"'''
        
        mock_file.return_value.read.return_value = content
        
        with patch('shutil.copy2') as mock_backup:
            success = self.app.process_filter_rules(
                rule_name="New Rule",
                header_field="from",
                value="new@example.com",
                dest_folder="imap://user@host.com/NewFolder"
            )
        
        self.assertTrue(success)
        mock_backup.assert_called_once()
    
    def test_process_filter_rules_invalid_header(self):
        """Test processing with invalid header field."""
        success = self.app.process_filter_rules(
            rule_name="Test Rule",
            header_field="invalid_field",
            value="test@example.com",
            dest_folder="imap://user@host.com/Folder"
        )
        
        self.assertFalse(success)
    
    def test_idempotency(self):
        """Test that adding the same condition twice doesn't create duplicates."""
        parser = MsgFilterParser()
        parser.version = "9"
        parser.logging = "no"
        
        # Create a rule with one condition
        rule = MsgFilterRule(
            name="Idempotency Test",
            enabled="yes",
            type="17",
            action="Move to folder",
            action_value="imap://user@host.com/Folder",
            condition="OR (from,contains,test@example.com)"
        )
        parser.rules = [rule]
        
        # Add the same condition again
        success = parser.add_condition_to_rule("Idempotency Test", "from", "test@example.com")
        self.assertTrue(success)
        
        # The condition should NOT have been duplicated
        expected_condition = "OR (from,contains,test@example.com)"
        self.assertEqual(parser.rules[0].condition, expected_condition)
        
        # Add a different condition
        success = parser.add_condition_to_rule("Idempotency Test", "subject", "urgent")
        self.assertTrue(success)
        
        # Should have both conditions
        expected_condition = "OR (from,contains,test@example.com) OR (subject,contains,urgent)"
        self.assertEqual(parser.rules[0].condition, expected_condition)
        
        # Try to add the first condition again
        success = parser.add_condition_to_rule("Idempotency Test", "from", "test@example.com")
        self.assertTrue(success)
        
        # Should still have the same two conditions (no duplicates)
        expected_condition = "OR (from,contains,test@example.com) OR (subject,contains,urgent)"
        self.assertEqual(parser.rules[0].condition, expected_condition)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete workflow."""
    
    def setUp(self):
        self.app = FilterAdderApp()
    
    def test_complete_workflow_new_rule(self):
        """Test the complete workflow for creating a new rule."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('''version="9"
logging="no"''')
            temp_file = f.name
        
        try:
            # Process the filter rules
            success = self.app.process_filter_rules(
                rule_name="Integration Test Rule",
                header_field="from",
                value="integration@example.com",
                dest_folder="imap://user@host.com/TestFolder",
                file_path=temp_file
            )
            
            self.assertTrue(success)
            
            # Verify the file was modified correctly
            with open(temp_file, 'r') as f:
                content = f.read()
            
            self.assertIn('name="Integration Test Rule"', content)
            self.assertIn('action="Move to folder"', content)
            self.assertIn('condition="OR (from,contains,integration@example.com)"', content)
            
        finally:
            # Clean up temporary file and any backup files
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            # Remove any backup files created during test
            backup_pattern = f"{temp_file}.backup_*"
            import glob
            for backup_file in glob.glob(backup_pattern):
                os.unlink(backup_file)
    
    def test_complete_workflow_existing_rule(self):
        """Test the complete workflow for modifying an existing rule."""
        # Create a temporary file with existing rule
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('''version="9"
logging="no"
name="Existing Rule"
enabled="yes"
type="17"
action="Move to folder"
actionValue="imap://user@host.com/Folder"
condition="OR (from,contains,existing@example.com)"''')
            temp_file = f.name
        
        try:
            # Process the filter rules
            success = self.app.process_filter_rules(
                rule_name="Existing Rule",
                header_field="subject",
                value="important",
                dest_folder="imap://user@host.com/Folder",
                file_path=temp_file
            )
            
            self.assertTrue(success)
            
            # Verify the file was modified correctly
            with open(temp_file, 'r') as f:
                content = f.read()
            
            self.assertIn('condition="OR (from,contains,existing@example.com) OR (subject,contains,important)"', content)
            
        finally:
            # Clean up temporary file and any backup files
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            # Remove any backup files created during test
            backup_pattern = f"{temp_file}.backup_*"
            import glob
            for backup_file in glob.glob(backup_pattern):
                os.unlink(backup_file)
    
    def test_complete_workflow_multiple_conditions(self):
        """Test the complete workflow for adding multiple conditions to a rule."""
        # Create a temporary file with an initial rule
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('''version="9"
logging="no"
name="Multi-Condition Rule"
enabled="yes"
type="17"
action="Move to folder"
actionValue="imap://user@host.com/Work"
condition="OR (from,contains,work@company.com)"''')
            temp_file = f.name
        
        try:
            # Add first additional condition
            success = self.app.process_filter_rules(
                rule_name="Multi-Condition Rule",
                header_field="subject",
                value="urgent",
                dest_folder="imap://user@host.com/Work",
                file_path=temp_file
            )
            self.assertTrue(success)
            
            # Add second additional condition
            success = self.app.process_filter_rules(
                rule_name="Multi-Condition Rule",
                header_field="to",
                value="team@company.com",
                dest_folder="imap://user@host.com/Work",
                file_path=temp_file
            )
            self.assertTrue(success)
            
            # Add third additional condition
            success = self.app.process_filter_rules(
                rule_name="Multi-Condition Rule",
                header_field="cc",
                value="manager@company.com",
                dest_folder="imap://user@host.com/Work",
                file_path=temp_file
            )
            self.assertTrue(success)
            
            # Verify the final file has all conditions
            with open(temp_file, 'r') as f:
                content = f.read()
            
            # Should have all 4 conditions in the rule
            expected_condition = 'condition="OR (from,contains,work@company.com) OR (subject,contains,urgent) OR (to,contains,team@company.com) OR (cc,contains,manager@company.com)"'
            self.assertIn(expected_condition, content)
            
            # Verify the rule structure is correct
            self.assertIn('name="Multi-Condition Rule"', content)
            self.assertIn('action="Move to folder"', content)
            self.assertIn('actionValue="imap://user@host.com/Work"', content)
            
        finally:
            # Clean up temporary file and any backup files
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            # Remove any backup files created during test
            backup_pattern = f"{temp_file}.backup_*"
            import glob
            for backup_file in glob.glob(backup_pattern):
                os.unlink(backup_file)
    
    def test_parser_multiple_conditions(self):
        """Test the parser's ability to handle multiple conditions in a rule."""
        parser = MsgFilterParser()
        parser.version = "9"
        parser.logging = "no"
        
        # Create a rule with multiple conditions
        rule = MsgFilterRule(
            name="Test Multi-Condition Rule",
            enabled="yes",
            type="17",
            action="Move to folder",
            action_value="imap://user@host.com/Folder",
            condition="OR (from,contains,test1@example.com) OR (subject,contains,test1) OR (to,contains,test1@example.com)"
        )
        parser.rules = [rule]
        
        # Add another condition
        success = parser.add_condition_to_rule("Test Multi-Condition Rule", "cc", "test2@example.com")
        self.assertTrue(success)
        
        # Add yet another condition
        success = parser.add_condition_to_rule("Test Multi-Condition Rule", "subject", "test2")
        self.assertTrue(success)
        
        # Verify the final condition has all 5 terms
        expected_condition = "OR (from,contains,test1@example.com) OR (subject,contains,test1) OR (to,contains,test1@example.com) OR (cc,contains,test2@example.com) OR (subject,contains,test2)"
        self.assertEqual(parser.rules[0].condition, expected_condition)
        
        # Test that we can parse this complex condition back
        parser2 = MsgFilterParser()
        parser2.version = "9"
        parser2.logging = "no"
        
        # Create a file content with the complex rule
        file_content = f'''version="9"
logging="no"
{parser.rules[0].to_string()}'''
        
        # Parse it back
        rules = parser2.parse_content(file_content)
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].name, "Test Multi-Condition Rule")
        self.assertEqual(rules[0].condition, expected_condition)
    



if __name__ == '__main__':
    unittest.main()
