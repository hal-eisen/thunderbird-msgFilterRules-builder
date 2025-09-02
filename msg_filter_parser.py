"""
Thunderbird message filter parser for msgFilterRules.dat files.

This module provides classes to parse and manipulate Thunderbird message filter rules.
"""

import logging
from typing import List, Optional

# Set up logging
logger = logging.getLogger(__name__)


class MsgFilterRule:
    """Represents a single Thunderbird message filter rule."""
    
    def __init__(self, name: str, enabled: str = "yes", type: str = "17",
                 action: str = "Move to folder", action_value: str = "",
                 condition: str = ""):
        self.name = name
        self.enabled = enabled
        self.type = type
        self.action = action
        self.action_value = action_value
        self.condition = condition
    
    def to_string(self) -> str:
        """Convert the rule back to string format for writing to file."""
        lines = [
            f'name="{self.name}"',
            f'enabled="{self.enabled}"',
            f'type="{self.type}"',
            f'action="{self.action}"',
            f'actionValue="{self.action_value}"',
            f'condition="{self.condition}"'
        ]
        return '\n'.join(lines)


class MsgFilterParser:
    """Parser for Thunderbird message filter rules files."""
    
    def __init__(self):
        self.version = ""
        self.logging = ""
        self.rules: List[MsgFilterRule] = []
    
    def parse_file(self, file_path: str) -> List[MsgFilterRule]:
        """Parse a msgFilterRules.dat file and return a list of rules."""
        logger.info(f"Parsing filter rules file: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.parse_content(content)
    
    def parse_content(self, content: str) -> List[MsgFilterRule]:
        """Parse the content of a msgFilterRules.dat file."""
        logger.debug("Parsing filter rules content")
        
        lines = content.strip().split('\n')
        current_rule = None
        rules = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse key-value pairs
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                # Handle global settings
                if key == 'version':
                    self.version = value
                    logger.debug(f"Found version: {value}")
                elif key == 'logging':
                    self.logging = value
                    logger.debug(f"Found logging: {value}")
                
                # Handle rule properties
                elif key == 'name':
                    # If we have a current rule, save it and start a new one
                    if current_rule:
                        rules.append(current_rule)
                        logger.debug(f"Completed rule: {current_rule.name}")
                    
                    current_rule = MsgFilterRule(name=value)
                    logger.debug(f"Starting new rule: {value}")
                
                elif current_rule:
                    if key == 'enabled':
                        current_rule.enabled = value
                    elif key == 'type':
                        current_rule.type = value
                    elif key == 'action':
                        current_rule.action = value
                    elif key == 'actionValue':
                        current_rule.action_value = value
                    elif key == 'condition':
                        current_rule.condition = value
        
        # Don't forget the last rule
        if current_rule:
            rules.append(current_rule)
            logger.debug(f"Completed final rule: {current_rule.name}")
        
        self.rules = rules
        logger.info(f"Parsed {len(rules)} rules from file")
        return rules
    
    def write_file(self, file_path: str, rules: Optional[List[MsgFilterRule]] = None) -> None:
        """Write rules to a msgFilterRules.dat file."""
        if rules is None:
            rules = self.rules
        
        logger.info(f"Writing {len(rules)} rules to file: {file_path}")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            # Write global settings
            if self.version:
                f.write(f'version="{self.version}"\n')
            if self.logging:
                f.write(f'logging="{self.logging}"\n')
            
            # Write rules
            for rule in rules:
                f.write(rule.to_string() + '\n')
        
        logger.info("Successfully wrote filter rules file")
    
    def find_rule_by_name(self, name: str) -> Optional[MsgFilterRule]:
        """Find a rule by its name."""
        for rule in self.rules:
            if rule.name == name:
                return rule
        return None
    
    def add_condition_to_rule(self, rule_name: str, header_field: str, value: str) -> bool:
        """Add a condition to an existing rule using OR logic (any match mode)."""
        rule = self.find_rule_by_name(rule_name)
        if not rule:
            logger.warning(f"Rule '{rule_name}' not found")
            return False
        
        logger.info(f"Adding condition to rule '{rule_name}': {header_field}={value}")
        
        # Parse existing condition
        if not rule.condition:
            # No existing condition, create new one
            rule.condition = f'OR ({header_field},contains,{value})'
        else:
            # Check if this condition already exists
            new_condition = f'({header_field},contains,{value})'
            if new_condition in rule.condition:
                logger.debug(f"Condition already exists: {new_condition}")
                return True  # Already exists, no change needed
            
            # Add to existing condition using OR logic
            # Add OR before the new condition
            rule.condition += f' OR ({header_field},contains,{value})'
        
        logger.debug(f"Updated condition: {rule.condition}")
        return True
    
    def create_new_rule(self, name: str, header_field: str, value: str, 
                       action_value: str) -> MsgFilterRule:
        """Create a new rule with the specified parameters."""
        logger.info(f"Creating new rule '{name}' with condition: {header_field}={value}")
        
        condition = f'OR ({header_field},contains,{value})'
        
        rule = MsgFilterRule(
            name=name,
            enabled="yes",
            type="17",
            action="Move to folder",
            action_value=action_value,
            condition=condition
        )
        
        self.rules.append(rule)
        logger.debug(f"Created rule: {rule.to_string()}")
        return rule
