# thunderbird-msgFilterRules-builder
# Thunderbird Message Filter Adder

A command-line tool to add message filters to Thunderbird's `msgFilterRules.dat` file. This tool allows you to easily create new filter rules or add conditions to existing rules using "any match" mode (OR logic).

Mine is located in /home/eisen/snap/thunderbird/common/.thunderbird/YOUR-PROFILE_-ID/ImapMail/imap.lxdn.org

## Features

- ✅ **Create new rules** with "Move to folder" action
- ✅ **Add conditions to existing rules** using OR logic (any match mode)
- ✅ **Idempotent operations** - running the same command twice won't create duplicates
- ✅ **Automatic backups** with timestamps before any changes
- ✅ **Header field validation** (from, to, cc, subject)
- ✅ **Comprehensive logging** with configurable verbosity
- ✅ **Safe file operations** with error handling

## Installation

This project uses `uv` for Python dependency management.

```bash
# Clone the repository
git clone <repository-url>
cd tbird-msg-filter-adder

# Install dependencies (uv will create a virtual environment)
uv sync
```

## Usage

### Basic Command Format

```bash
uv run main.py --rule-name=RULENAME --header-field=HEADERFIELD --value=VALUE --dest-folder=DESTFOLDER
```

### Parameters

- `--rule-name`: Name of the filter rule (required)
- `--header-field`: Email header field to match (required)
  - Valid values: `from`, `to`, `cc`, `subject`
- `--value`: Value to match in the header field (required)
- `--dest-folder`: Destination folder URI for moving messages (required)
- `--file-path`: Path to msgFilterRules.dat file (optional, defaults to Thunderbird profile)
- `--verbose, -v`: Enable verbose logging (optional)

### Examples

#### Create a New Rule

```bash
# Create a rule to move newsletters to a Promotions folder
uv run main.py \
  --rule-name="Newsletters" \
  --header-field=from \
  --value=newsletter@example.com \
  --dest-folder="imap://user@host.com/Promotions"
```

#### Add Condition to Existing Rule

```bash
# Add another newsletter sender to the existing rule
uv run main.py \
  --rule-name="Newsletters" \
  --header-field=from \
  --value=another-newsletter@example.com \
  --dest-folder="imap://user@host.com/Promotions"
```

#### Work-Related Filters

```bash
# Create a rule for work emails
uv run main.py \
  --rule-name="Work" \
  --header-field=subject \
  --value="urgent" \
  --dest-folder="imap://user@host.com/Work" \
  --verbose

# Add more conditions to the work rule
uv run main.py \
  --rule-name="Work" \
  --header-field=to \
  --value=team@company.com \
  --dest-folder="imap://user@host.com/Work"
```

#### Using Custom File Path

```bash
# Use a specific msgFilterRules.dat file
uv run main.py \
  --rule-name="Test Rule" \
  --header-field=from \
  --value=test@example.com \
  --dest-folder="imap://user@host.com/Test" \
  --file-path="/path/to/custom/msgFilterRules.dat"
```

## How It Works

### Rule Creation vs. Modification

- **If the rule doesn't exist**: Creates a new rule with the specified condition
- **If the rule exists**: Adds the new condition to the existing rule using OR logic
- **Idempotent**: Running the same command multiple times won't create duplicate conditions

### Condition Format

The tool uses "any match" mode (OR logic) for all conditions:

```
OR (field,contains,value)
```

For multiple conditions:
```
OR (from,contains,email1@example.com) OR (subject,contains,urgent) OR (to,contains,team@company.com)
```

### File Structure

The tool modifies Thunderbird's `msgFilterRules.dat` file, which uses this format:

```
version="9"
logging="no"
name="Rule Name"
enabled="yes"
type="17"
action="Move to folder"
actionValue="imap://user@host.com/Folder"
condition="OR (from,contains,value)"
```

### Backup System

Before making any changes, the tool automatically creates a timestamped backup:

```
msgFilterRules.dat.backup_20250828_175430
```

## Development

This project follows Test-Driven Development (TDD) principles.

### Running Tests

```bash
# Run all tests
uv run python test_msg_filter_parser.py
uv run python test_main_app.py

# Run with verbose output
uv run python -m pytest test_main_app.py -v
```

### Project Structure

```
tbird-msg-filter-adder/
├── main.py                 # Command-line interface
├── msg_filter_parser.py    # Core parsing and manipulation logic
├── test_msg_filter_parser.py  # Parser unit tests
├── test_main_app.py        # Application integration tests
├── example-msgFilterRules.dat  # Example file (read-only)
├── pyproject.toml          # Project configuration
└── README.md              # This file
```

## Technical Details

### Thunderbird Profile Location

Default location for the `msgFilterRules.dat` file:
```
/home/eisen/snap/thunderbird/common/.thunderbird/8blc452o.default/ImapMail/imap.lxdn.org/msgFilterRules.dat
```

### Supported Header Fields

- `from`: Sender email address
- `to`: Recipient email address  
- `cc`: Carbon copy recipients
- `subject`: Email subject line

### Action Type

This tool always uses "Move to folder" action, as specified in the requirements.

### Mode Types

- **OR mode** (any match): Any condition can match - this is what we use
- **AND mode** (all match): All conditions must match - avoided as per requirements

## Key Findings from Thunderbird Source Code Analysis

### File Format Structure
- The `msgFilterRules.dat` file uses a simple key-value format with quoted strings
- Each rule is a series of key-value pairs, one per line
- File starts with global settings: `version` and `logging`
- Rules are separated by their properties (name, enabled, type, action, etc.)

### Rule Properties
- `name`: The filter rule name (string)
- `enabled`: Whether the rule is active ("yes"/"no")
- `type`: Rule type identifier (typically "17" for standard rules)
- `action`: Action to perform (e.g., "Move to folder", "Copy to folder")
- `actionValue`: Target folder URI for move/copy actions
- `condition`: Search criteria in format "AND/OR (field,operator,value)"

### Action Types (from nsMsgFilter.cpp)
- "Move to folder" - Move messages to specified folder
- "Copy to folder" - Copy messages to specified folder
- "Change priority" - Change message priority
- "Delete" - Delete messages
- "Mark read" - Mark messages as read
- "Mark flagged" - Mark messages as flagged
- "Reply" - Auto-reply to messages
- "Forward" - Forward messages
- "Stop execution" - Stop processing further rules
- "AddTag" - Add tags to messages
- "Custom" - Custom filter actions

### Condition Format
- Format: `"AND/OR (field,operator,value)"`
- Multiple terms: `"AND (field1,op1,val1) (field2,op2,val2)"`
- Operators: "contains", "doesn't contain", "is", "isn't", "is empty", etc.
- Fields: "from", "to", "cc", "subject", "body", "date", etc.

### Header Field Validation
- Standard fields: from, to, cc, subject
- Custom headers are supported with quoted format: `"X-Custom-Header"`
- Field names are case-insensitive

### Mode Types
- "AND" mode: All conditions must match (all match)
- "OR" mode: Any condition can match (any match) - this is what we use
- Avoid "all mode" as specified in requirements
