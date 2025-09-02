#!/usr/bin/env python3
"""
Thunderbird Message Filter Adder

A command-line tool to add message filters to Thunderbird's msgFilterRules.dat file.
"""

import argparse
import logging
import os
import shutil
from datetime import datetime
from typing import Optional

from msg_filter_parser import MsgFilterParser


class FilterAdderApp:
    """Main application class for adding Thunderbird message filters."""
    
    def __init__(self, verbose: bool = False):
        self.parser = MsgFilterParser()
        self.default_file_path = "/home/eisen/snap/thunderbird/common/.thunderbird/8blc452o.default/ImapMail/imap.lxdn.org/msgFilterRules.dat"
        
        # Set up logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def validate_header_field(self, header_field: str) -> bool:
        """Validate that the header field is one of the allowed values."""
        valid_fields = ["from", "to", "cc", "subject"]
        return header_field.lower() in valid_fields
    
    def create_backup_path(self, file_path: str) -> str:
        """Create a backup file path with timestamp."""
        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{filename}.backup_{timestamp}"
        return os.path.join(directory, backup_filename)
    
    def backup_file(self, file_path: str) -> bool:
        """Create a backup of the filter rules file."""
        try:
            backup_path = self.create_backup_path(file_path)
            shutil.copy2(file_path, backup_path)
            self.logger.info(f"Created backup: {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return False
    
    def process_filter_rules(self, rule_name: str, header_field: str, value: str, 
                           dest_folder: str, file_path: Optional[str] = None) -> bool:
        """Process the filter rules file to add or modify a rule."""
        if file_path is None:
            file_path = self.default_file_path
        
        # Validate header field
        if not self.validate_header_field(header_field):
            self.logger.error(f"Invalid header field: {header_field}. Must be one of: from, to, cc, subject")
            return False
        
        # Check if file exists
        if not os.path.exists(file_path):
            self.logger.error(f"Filter rules file not found: {file_path}")
            return False
        
        try:
            # Create backup
            if not self.backup_file(file_path):
                return False
            
            # Parse existing rules
            self.parser.parse_file(file_path)
            
            # Check if rule already exists
            existing_rule = self.parser.find_rule_by_name(rule_name)
            
            if existing_rule:
                self.logger.info(f"Rule '{rule_name}' already exists, adding condition")
                # Add condition to existing rule
                success = self.parser.add_condition_to_rule(rule_name, header_field, value)
                if not success:
                    self.logger.error(f"Failed to add condition to rule '{rule_name}'")
                    return False
            else:
                self.logger.info(f"Creating new rule '{rule_name}'")
                # Create new rule
                self.parser.create_new_rule(rule_name, header_field, value, dest_folder)
            
            # Write updated rules back to file
            self.parser.write_file(file_path)
            self.logger.info(f"Successfully updated filter rules file")
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing filter rules: {e}")
            return False


def main():
    """Main entry point for the command-line interface."""
    parser = argparse.ArgumentParser(
        description="Add message filters to Thunderbird's msgFilterRules.dat file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --rule-name="Newsletters" --header-field=from --value=newsletter@example.com --dest-folder="imap://user@host.com/Newsletters"
  %(prog)s --rule-name="Work" --header-field=subject --value=urgent --dest-folder="imap://user@host.com/Work" --verbose
        """
    )
    
    parser.add_argument(
        "--rule-name",
        required=True,
        help="Name of the filter rule"
    )
    
    parser.add_argument(
        "--header-field",
        required=True,
        choices=["from", "to", "cc", "subject"],
        help="Email header field to match"
    )
    
    parser.add_argument(
        "--value",
        required=True,
        help="Value to match in the header field"
    )
    
    parser.add_argument(
        "--dest-folder",
        required=True,
        help="Destination folder URI for moving messages"
    )
    
    parser.add_argument(
        "--file-path",
        help="Path to msgFilterRules.dat file (default: Thunderbird profile location)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Create and run the application
    app = FilterAdderApp(verbose=args.verbose)
    
    success = app.process_filter_rules(
        rule_name=args.rule_name,
        header_field=args.header_field,
        value=args.value,
        dest_folder=args.dest_folder,
        file_path=args.file_path
    )
    
    if success:
        print(f"Successfully processed filter rule '{args.rule_name}'")
        return 0
    else:
        print(f"Failed to process filter rule '{args.rule_name}'")
        return 1


if __name__ == "__main__":
    exit(main())
