# Drudge CLI Tool - Professional Python Package Edition

[![GitHub](https://img.shields.io/badge/GitHub-Trik16%2Fdrudge-blue?logo=github)](https://github.com/Trik16/drudge)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Typer](https://img.shields.io/badge/CLI-Typer-green.svg)](https://typer.tiangolo.com/)

A comprehensive, professionally architected command-line tool for tracking work time on tasks with organized daily logs.
Built with modern Python package structure, Typer CLI framework, Rich formatting, type hints, dataclasses, and enterprise-level architectural patterns.

**🎯 Production Ready**: Complete package refactor with modular architecture, centralized validation, configuration management, structured logging, and comprehensive unit tests ensuring reliability and maintainability.

## 🏗️ Package Architecture

### Modern Python Package Structure
```
src/worklog/
├── __init__.py          # Package initialization and public API
├── __main__.py          # Entry point for python -m worklog
├── models.py            # Data models (TaskEntry, PausedTask, WorkLogData)
├── config.py            # Configuration management (WorkLogConfig)
├── validators.py        # Centralized input validation
├── managers/            # Business logic managers
│   ├── __init__.py
│   ├── worklog.py       # Core WorkLog class
│   ├── backup.py        # Backup management
│   └── daily_file.py    # Daily file operations
├── cli/                 # Command-line interface
│   ├── __init__.py
│   └── commands.py      # Typer command definitions
└── utils/               # Utility functions
    ├── __init__.py
    └── decorators.py    # Common decorators (@auto_save, @requires_data)
```

## 🚀 Major Refactoring Accomplishments

### ✅ Advanced Architecture Improvements
This version represents a **comprehensive architectural refactor** with modern software engineering practices:

#### **Separation of Concerns**
- **WorkLogValidator**: Centralized validation logic for dates, times, and task names
- **WorkLogConfig**: Configuration management with dataclass for customizable settings
- **BackupManager**: Specialized backup creation and management
- **DailyFileManager**: Dedicated daily file operations and formatting
- **Structured Logging**: Professional logging system with configurable levels
- **Modular Package**: Clean separation into models, managers, CLI, and utilities

#### **Performance & Reliability**
- **Caching**: `@lru_cache` decorators for frequently accessed methods
- **Enhanced Error Handling**: User-friendly error messages with detailed logging
- **Atomic Operations**: Safe file writes preventing data corruption
- **Comprehensive Validation**: Input validation at multiple layers
- **Memory Efficiency**: Optimized file operations and data structures
- **Type Safety**: Full type hints throughout the codebase

## Installation

### Prerequisites
- Python 3.8+ (developed with Python 3.13)
- Required packages: `typer[all]` and `rich`

### Setup
1. Install required dependencies:
   ```bash
   pip install typer[all] rich
   ```

2. Install the package in development mode:
   ```bash
   cd /path/to/WorkLog
   pip install -e .
   ```

3. Or run directly as a module:
   ```bash
   python3 -m src.worklog --help
   ```

4. Create a shell alias for convenience:
   ```bash
   # Run the setup script
   ./setup_drudge_alias.sh
   
   # Or add manually to your shell config
   echo 'alias drudge="python3 -m src.worklog"' >> ~/.zshrc
   source ~/.zshrc
   ```
   ```bash
   cat setup_alias.sh >> ~/.zshrc
   source ~/.zshrc
   ```

## Architecture Components

### 🏗️ Core Classes & Managers

#### **WorkLogValidator**
Centralized validation logic eliminating code duplication:
```python
# Validates dates, times, task names with clear error messages
validator = WorkLogValidator()
validator.validate_date_format("2023-12-31", config)
validator.validate_time_format("14:30")  # Returns (hours, minutes)
validator.validate_task_name("My Task")  # Checks length and characters
```

#### **WorkLogConfig** 
Configuration management with sensible defaults:
```python
config = WorkLogConfig(
    worklog_dir_name='.worklog',     # Customizable directory name
    max_recent_tasks=10,             # Configurable history length
    backup_enabled=True,             # Safety features
    display_time_format="%Y-%m-%d %H:%M:%S"  # Flexible formatting
)
```

#### **BackupManager**
Specialized backup operations for data safety:
- Creates comprehensive backups before destructive operations
- Handles both JSON entries and daily file content
- Consistent backup format with timestamps

#### **DailyFileManager**  
Dedicated daily file operations:
- Consistent entry formatting across all operations
- Chronological ordering maintenance
- Duplicate entry handling for task completions

#### **Structured Logging**
Professional logging system:
```python
import logging
logger = logging.getLogger('worklog')
logger.info("Task started successfully")
logger.error("Data corruption detected")
```

### 🔧 Performance Optimizations
- **@lru_cache decorators**: Caches frequently called formatting methods
- **Atomic file operations**: Prevents data corruption during saves  
- **Optimized data structures**: Efficient task lookup and management
- **Lazy loading**: Data loaded only when needed

### Modern CLI Interface
The new version uses **Typer** instead of argparse, providing:
- 🎨 **Rich formatting** with colors and beautiful tables
- 📖 **Automatic help generation** with detailed command descriptions
- ✅ **Type safety** with comprehensive type hints
- 🚀 **Command-based interface** for better organization

## Usage

### Modern Command Interface
All commands now use the modern Typer syntax with rich formatting and emojis:

### Basic Task Tracking
- **Start a task**: `drudge start "Task Name"`
- **End a task**: `drudge end "Task Name"`
- **Custom start time**: `drudge start "Task Name" --time 09:30`
- **Force start** (auto-end active): `drudge start "New Task" --force`
- **Pause a task**: `drudge pause "Task Name"`
- **Resume a task**: `drudge resume "Task Name"`

### Viewing Work History
- **Show current status**: `drudge status`
- **List recent tasks**: `drudge recent`
- **List entries**: `drudge list`
- **Filter by date**: `drudge list --date 2025-10-03`
- **Filter by task**: `drudge list --task "bug"`
- **Daily summary**: `drudge daily`
- **Specific date summary**: `drudge daily --date 2025-10-03`

### Configuration and Help
- **Show configuration**: `drudge config`
- **Show version**: `drudge version`
- **Main help**: `drudge --help`
- **Command help**: `drudge start --help`

## Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `drudge start "Name"` | 🚀 Start a new task | `drudge start "Bug fix #123"` |
| `drudge start "Name" --time HH:MM` | 🚀 Start task at specific time | `drudge start "Meeting" --time 09:30` |
| `drudge start "Name" --force` | 🚀 Force start (auto-end active tasks) | `drudge start "Review" --force` |
| `drudge end "Name"` | 🏁 End an active task | `drudge end "Bug fix #123"` |
| `drudge end "Name" --time HH:MM` | 🏁 End task at specific time | `drudge end "Meeting" --time 17:30` |
| `drudge pause "Name"` | ⏸️ Pause an active task | `drudge pause "Task"` |
| `drudge resume "Name"` | ▶️ Resume a paused task | `drudge resume "Task"` |
| `drudge status` | 📊 Show current work status | `drudge status` |
| `drudge recent` | 📝 List recent tasks | `drudge recent` |
| `drudge recent --limit N` | 📝 Show N recent tasks | `drudge recent --limit 10` |
| `drudge list` | 📋 List completed entries | `drudge list` |
| `drudge list --date YYYY-MM-DD` | � List entries for specific date | `drudge list --date 2025-10-03` |
| `drudge list --task "keyword"` | � Filter entries by task name | `drudge list --task "bug"` |
| `drudge daily` | 📅 Show today's summary | `drudge daily` |
| `drudge daily --date YYYY-MM-DD` | 📅 Show specific date summary | `drudge daily --date 2025-10-03` |
| `drudge config` | ⚙️ Show configuration | `drudge config` |
| `drudge version` | 📦 Show version info | `drudge version` |
| `drudge --help` | ❓ Show help message | `drudge --help` |

## Examples

```bash
# Start tracking a task
$ drudge start "Morning emails"
🚀 Started 'Morning emails' at 2025-10-03 09:00:00

# End the task
$ drudge end "Morning emails"
🏁 Completed 'Morning emails' at 2025-10-03 09:30:00 (Duration: 00:30:00)

# Start a new task with custom time
$ drudge start "Fix bug #123" --time 10:00
🚀 Started 'Fix bug #123' at 2025-10-03 10:00:00

# Check current status
$ drudge status
🚀 Active Tasks:
  • Fix bug #123 (Running: 00:30:00)

📊 Completed today: 1 tasks

# Pause a task (for lunch, meeting, etc.)
$ drudge pause "Fix bug #123"
⏸️ Paused 'Fix bug #123' at 2025-10-03 12:00:00

# Resume the task
$ drudge resume "Fix bug #123"
▶️ Resumed 'Fix bug #123' at 2025-10-03 13:00:00

# Complete the task
$ drudge end "Fix bug #123"
🏁 Completed 'Fix bug #123' at 2025-10-03 17:00:00 (Duration: 05:00:00)

# View daily summary
$ drudge daily
📅 Daily Summary for 2025-10-03
📊 Total: 2 tasks, 5h 30m

📋 Tasks:
  • Fix bug #123: 5h 0m
  • Morning emails: 0h 30m

# List recent tasks for quick reference
$ drudge recent
� Recent Tasks:
  1. Fix bug #123
  2. Morning emails
  3. Code review

# View recent work (with rich formatting)
$ worklog recent
### Recent entries (using short options)
```bash
# Show recent entries (default 10)
$ worklog recent

# Show specific number using short option
$ worklog recent -c 5
📊 Recent 5 entries:

  2025-10-03 14:00:00 Code review (01:30:15)
  2025-10-03 10:30:00 Fix bug #123 (03:00:00)
  2025-10-03 09:00:00 Team standup (00:30:00)
  # ... and so on
```

# View today's work
$ worklog today
📅 Today's worklog (2025-10-03):

2025-10-03 14:30:15 Fix bug #123 (01:15:07)
2025-10-03 16:00:00 Code review (00:30:45)
2025-10-03 17:15:30 Meeting prep [ACTIVE]

# View work from a specific date
$ worklog date 2025-10-02
📅 Worklog for 2025-10-02:

2025-10-02 09:00:00 Sprint planning (01:30:00)
2025-10-02 11:15:00 Development work (03:45:20)

# Custom start times (backdate entries)
$ worklog task "Morning meeting" --start-time 09:00
✅ Started tracking: 'Morning meeting' at 2025-10-03 09:00:00

$ worklog start --start-time 08:30
✅ Started tracking: '[ANONYMOUS WORK]' at 2025-10-03 08:30:00
💡 Use 'worklog task "Task Name"' to assign a name to this session

# Clean today's worklog (with backup)
$ worklog clean
🔍 Found 15 entries for 2025-10-03
📄 Daily file: /home/karim/.worklog/2025-10-03.txt
Are you sure you want to clean today's worklog? [y/N]: y
💾 Backup created: /home/karim/.worklog/2025-10-03_backup.txt
✅ Cleaned 15 JSON entries
🗑️  Removed daily file: /home/karim/.worklog/2025-10-03.txt
✨ Clean completed for 2025-10-03

# Clean specific date worklog (with backup)
$ worklog clean --date 2025-10-01
🔍 Found 8 entries for 2025-10-01
Are you sure you want to clean worklog for 2025-10-01? [y/N]: y
💾 Backup created: /home/karim/.worklog/2025-10-01_backup.txt
✅ Cleaned 8 JSON entries
✨ Clean completed for 2025-10-01

# Clean using short option
$ worklog clean -d 2025-09-30
ℹ️  No worklog entries found for 2025-09-30
```

## Data Storage

### Directory Structure
- **`~/.worklog/`** - Main worklog directory
- **`~/.worklog/worklog.json`** - Comprehensive task database (machine-readable)
- **`~/.worklog/YYYY-MM-DD.txt`** - Daily readable logs (human-readable)

### File Formats
- **JSON Database**: Complete task history with precise timestamps and metadata
- **Daily Files**: Clean, readable format per day showing:
  - `YYYY-MM-DD HH:MM:SS Task Name (HH:MM:SS)` for completed tasks
  - `YYYY-MM-DD HH:MM:SS Task Name [ACTIVE]` for ongoing tasks

### Migration
- Automatically migrates existing `~/.worklog.json` to new directory structure
- Preserves all historical data during upgrade

## Features

- **Single-task mode by default**: Focus on one task at a time (typical workflow)
- **Optional parallel mode**: Use `--parallel` flag for concurrent tasks when needed
- **Smart task switching**: Starting new task automatically stops previous one
- **Enhanced --stop command**: Clears both active AND paused tasks completely  
- **Smart --list command**: Shows today's log when no active tasks
- **Automatic duration calculation**: Precisely tracks time spent on tasks
- **Anonymous work sessions**: Start working before knowing the task name
- **Pause/Resume functionality**: Interrupt tasks and continue later
- **Batch operations**: Stop or pause all tasks with single command
- **Custom start times**: Backdate entries with `--start-time HH:MM` format
- **Clean worklog command**: Remove today's entries or specific date entries with backup and confirmation
- **Rich formatting**: Beautiful console output with colors, emojis, and tables
- **Modern CLI**: Typer-based interface with automatic help generation
- **Type safety**: Comprehensive type hints and dataclass structures
- **Organized daily files**: Separate readable file for each day
- **Persistent storage**: Data survives system restarts
- **Clean compact format**: Easy to read timestamps and durations
- **Date-specific viewing**: View work history for any specific date
- **Flexible task naming**: Convert anonymous sessions to named tasks retroactively
- **Session tracking**: Multiple work sessions per task are properly tracked
- **Error handling**: Graceful handling of corrupted data files
- **Data safety**: Backup creation before destructive operations
- **Input validation**: Robust time format validation with clear error messages
- **Extensible design**: JSON + daily files ready for future integrations

## Short Options Reference

For convenience, all major options have short aliases:

| Long Option | Short Options | Description |
|-------------|---------------|-------------|
| `--parallel` | `-p`, `-pl` | Allow multiple concurrent tasks |
| `--start-time` | `-t` | Custom start time (HH:MM) |
| `--count` | `-c` | Number of recent entries to show |
| `--date` | `-d` | Specific date for clean command (YYYY-MM-DD) |

### Command Examples with Short Options
```bash
# Start task in parallel mode with custom time
$ worklog task "Meeting" -p -t 14:30

# Show recent 5 entries
$ worklog recent -c 5

# Start anonymous session with time
$ worklog start -t 09:00

# Clean specific date
$ worklog clean -d 2025-10-01
```

## File Structure Example

```
~/.worklog/
├── worklog.json          # Complete database
├── 2025-10-01.txt       # Daily readable logs
├── 2025-10-02.txt
├── 2025-10-03.txt
└── ...
```

### Daily File Content Example
```
2025-10-03 09:00:00 Email and Planning (02:15:30)
2025-10-03 11:15:30 Bug fix #456 (01:30:00)
2025-10-03 14:30:00 Bug fix #456 (00:45:45)
2025-10-03 16:00:00 Documentation [ACTIVE]
```

Note: Tasks with pause/resume show multiple entries, each representing a work session.

### Advanced Workflows

#### Anonymous Work Session
```
# Start your day without knowing the first task
$ worklog --start

# Later, when you know what you were actually working on
$ worklog "Morning emails and planning"

# The time tracking starts from the --start time, not when you named it
```

#### Pause/Resume Workflow
```
# Working on a task
$ worklog "Important project"

# Need to pause for meeting/lunch
$ worklog --pause
Paused 1 task(s):
  - Important project (session: 02:30:15)

# Resume after interruption (two ways to do this)
$ worklog --resume    # Resume last paused task
# OR
$ worklog --start     # Also resumes if there are paused tasks

# Continue working and finish
$ worklog "Important project"
Finished task: 'Important project' at 2025-10-03 17:00:00
Duration: 01:30:45
```

#### Single-Task vs Parallel Mode
```
# Default: Single-task mode (most common)
$ worklog "Task A"
$ worklog "Task B"  # Automatically stops Task A
Stopped previous task(s) (single-task mode):
  - Task A (01:15:30)

# Explicit: Parallel mode (when you need multiple tasks)
$ worklog "Task A"
$ worklog "Task B" --parallel  # Keeps Task A running
$ worklog "Task C" --parallel  # All three tasks now active
```

## Technical Features & Architecture

### Modern Python Implementation
- **Python 3.8+**: Utilizes modern Python features and type system
- **Dataclasses**: Structured data with `TaskEntry`, `PausedTask`, and `WorkLogData`
- **Type hints**: Full type annotation for better IDE support and code safety
- **Property decorators**: Lazy loading and computed properties
- **Context managers**: Safe file operations with automatic cleanup
- **Decorators**: `@requires_data` and `@auto_save` for clean separation of concerns

### CLI Excellence with Typer
- **Rich formatting**: Beautiful console output with colors and emojis
- **Automatic help**: Generated help text with command descriptions
- **Command-based**: Logical organization of functionality
- **Type safety**: Automatic validation of arguments and options

## Testing & Quality Assurance

### Comprehensive Test Suite
The refactored WorkLog tool includes a complete unit test suite ensuring reliability:

```bash
# Run the updated comprehensive test suite
python3 test_worklog_updated.py

# Test results: 28 tests, 0 failures, 0 errors ✅
```

#### Test Coverage Areas
- **WorkLogValidator**: Centralized validation logic testing
- **WorkLogConfig**: Configuration management validation  
- **Data Classes**: TaskEntry, PausedTask, WorkLogData validation
- **Core Operations**: Task starting, stopping, ending functionality
- **Session Management**: Pause, resume, stop-all operations with new API
- **Time Handling**: Parsing, formatting, duration calculations with ISO timestamps
- **CLI Integration**: Typer commands and modern interface validation
- **Data Persistence**: File operations, loading, saving with enhanced error handling
- **Integration Scenarios**: Complete workflow testing with new architecture
- **Error Handling**: Enhanced validation and user-friendly error messages

#### Quality Improvements
- **Updated Test Suite**: All tests updated to match refactored API
- **Architectural Testing**: New classes and managers thoroughly tested
- **Modern Test Patterns**: Uses proper mocking and isolated test environments
- **Enhanced Validation Testing**: Comprehensive input validation coverage
- **Error Recovery Testing**: Validates graceful handling of edge cases

### Future Integration Notes
The tool is designed with extensibility in mind:
- **Dual storage format**: JSON for programmatic access, TXT for human reading
- **Modular class structure**: Clean `WorkLog` class with comprehensive docstrings
- **Date-organized files**: Perfect for daily standup reports and time tracking
- **Timestamp format**: ISO format compatible with most APIs and databases
- **Extensible design**: Easy to add fields like project, client, tags, or API integrations
- **Error handling**: Comprehensive error handling with user-friendly messages
- **Directory structure**: Organized for easy parsing and backup
- **Test-driven development**: Full test coverage ensures safe future modifications

## Development & Files

### Project Structure
```
WorkLog/
├── worklog.py                     # Main CLI tool with advanced architecture
├── worklog_original.py            # Original implementation backup
├── worklog_argparse_backup.py     # Pre-refactor backup
├── test_worklog_updated.py        # Updated comprehensive test suite (28 tests)
├── test_worklog.py                # Original test suite (reference)
├── test_refactoring.py            # Refactoring validation tests
├── simple_test.py                 # Basic functionality verification
├── requirements.txt               # Python dependencies  
├── README.md                      # This comprehensive documentation
└── setup_alias.sh                 # Shell alias setup script
```

### Key Files
- **`worklog.py`**: Production-ready implementation with advanced architecture
- **`test_worklog_updated.py`**: Complete test suite for refactored code
- **`test_refactoring.py`**: Validation tests for new architecture components  
- **`simple_test.py`**: Quick functionality verification
- **`requirements.txt`**: Dependencies (typer[all], rich)
- **Backup files**: Original implementations preserved for reference

### Running Tests
```bash
# Updated comprehensive test suite (recommended)
python3 test_worklog_updated.py

# Quick functionality verification
python3 simple_test.py

# Architecture validation tests
python3 test_refactoring.py

# Original test suite (for reference)
python3 -m unittest test_worklog.py -v
```

## 🎯 Refactoring Summary

This refactoring demonstrates modern Python development practices:

1. **Separation of Concerns**: Specialized classes for validation, configuration, backup management, and daily file operations
2. **Centralized Logic**: Eliminated code duplication through centralized validation and configuration
3. **Enhanced Error Handling**: User-friendly error messages with comprehensive logging
4. **Performance Optimization**: Caching and optimized file operations
5. **Maintainable Architecture**: Clean class structure with clear responsibilities
6. **Comprehensive Testing**: Updated test suite covering all new functionality
7. **Professional Standards**: Structured logging, atomic operations, and robust data validation

The result is a more maintainable, reliable, and extensible codebase while preserving all original functionality.