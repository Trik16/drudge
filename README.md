# Drudge CLI - Professional Work Time Tracking Tool

[![GitHub](https://img.shields.io/badge/GitHub-Trik16%2Fdrudge-blue?logo=github)](https://github.com/Trik16/drudge)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![PyPI](https://img.shields.io/pypi/v/drudge-cli.svg)](https://pypi.org/project/drudge-cli/)
[![Python](https://img.shields.io/pypi/pyversions/drudge-cli.svg)](https://pypi.org/project/drudge-cli/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.1.1-blue.svg)](https://github.com/Trik16/drudge/releases)
[![Tests](https://github.com/Trik16/drudge/actions/workflows/test.yml/badge.svg)](https://github.com/Trik16/drudge/actions/workflows/test.yml)

A comprehensive, professionally architected command-line tool for tracking work time on tasks with organized daily logs. Built with modern Python package structure, Typer CLI framework, Rich formatting, type hints, dataclasses, and enterprise-level architectural patterns.

**🎯 Version 2.1.1 - Enhanced CLI**: Native help system, enhanced end command with --all flag, and powerful clean command for worklog management.

## ✨ Key Features

### 🚀 Task Management
- **Smart task tracking**: Start, end, pause, and resume tasks
- **Anonymous work sessions**: Start working without naming the task
- **Single-task mode**: Auto-ends previous tasks (default behavior)
- **Parallel mode**: Work on multiple tasks simultaneously with `--parallel` flag
- **Custom timestamps**: Backdate entries with `--time HH:MM`
- **Pause/Resume**: Interrupt work and continue later

### 📊 Reporting & Views
- **Unified list command**: See active, paused, and completed tasks at a glance
- **Recent tasks**: View detailed recent work history
- **Daily summaries**: Time totals and task breakdown by day
- **Flexible filtering**: By date, task name, or custom limits

### 🗑️ **NEW in v2.1.0**: Clean Command
- **Clean by date**: Remove all entries for a specific date
- **Clean by task**: Remove all entries for a task across all dates
- **Selective cleaning**: Clean task entries for specific date only
- **Clean all**: Reset entire worklog with confirmation
- **Automatic backups**: Safety first - backups before deletion

### 🏁 **ENHANCED in v2.1.0**: End Command
- **Default**: `drudge end` - Ends only active tasks
- **New --all flag**: `drudge end --all` - Ends active AND paused tasks

### ❓ **IMPROVED in v2.1.0**: Help System
- Native Typer `--help` integration
- Command-specific help: `drudge COMMAND --help`
- Consistent with standard CLI conventions

## 📦 Installation

### Prerequisites
- Python 3.8+ (tested with Python 3.10 and 3.13)
- Required packages: `typer[all]` and `rich`

### Install from PyPI
```bash
pip install drudge-cli
```

### Install from Source
```bash
# Clone the repository
git clone https://github.com/Trik16/drudge.git
cd drudge

# Install in development mode
pip install -e .
```

### Setup Shell Alias
```bash
# Run the setup script
./setup_drudge_alias.sh

# Or add manually to your shell config
echo 'alias drudge="python3 -m src.worklog"' >> ~/.zshrc
source ~/.zshrc
```

## 🚀 Quick Start

```bash
# Start your workday
drudge start "Morning emails"

# Check what's active
drudge list

# End the task
drudge end "Morning emails"

# View today's summary
drudge daily
```

## ⚙️ Configuration

### Config File

Drudge can be configured using a YAML file located at `~/.worklog/config.yaml`. This allows you to customize behavior, define project categories, and enable integrations like **Haunts** (Google Calendar sync).

### Creating Configuration

```bash
# Interactive setup wizard (recommended)
drudge config --setup

# Show current configuration
drudge config --show

# Edit configuration file
drudge config --edit
```

The `--setup` wizard will:
- Detect existing **Haunts** installation
- Import Google Sheet document ID automatically
- Guide you through project categorization
- Configure sync preferences

### Configuration Structure

```yaml
# Basic settings
worklog_directory: "~/.worklog"
sheet_document_id: "1A2B3C4D5E6F7G8H9I0J"
timezone: "Europe/Rome"

# Project categorization
projects:
  - Backend
  - Frontend
  - DevOps
  - Research

# Google Sheets sync (haunts-compatible format)
google_sheets:
  enabled: true
  auto_sync: false
  round_hours: 0.5      # Round to 15min (0.25), 30min (0.5), hour (1.0)

# Optional: Haunts integration (for Calendar sync)
haunts:
  enabled: false
  config_path: "~/.haunts"
```

### Configuration Parameters

#### Basic Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `worklog_directory` | string | `~/.worklog` | Directory for worklog data |
| `sheet_document_id` | string | - | Google Sheets document ID (shared) |
| `timezone` | string | system | Timezone (from haunts or system) |

#### Projects

Define project categories to organize your work entries. Projects can be assigned when starting tasks:

```bash
# Start a task with project categorization
drudge start "Implement login feature" --project Backend
drudge start "Fix CSS layout" --project Frontend
```

#### Google Sheets Integration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | boolean | `false` | Enable/disable Google Sheets sync |
| `auto_sync` | boolean | `false` | Auto-sync on task end |
| `round_hours` | float | `0.5` | Rounding: 0.25 (15min), 0.5 (30min), 1.0 (hour) |

**Note:** Decimal places are automatic: 0.25→2 decimals, 0.5→1 decimal, 1.0→0 decimals

#### Haunts Integration (Optional)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | boolean | `false` | Whether you use haunts for Calendar sync |
| `config_path` | string | `~/.haunts` | Path to haunts config (reference only) |

**Note:** Haunts is optional. If enabled, it reads the Google Sheet and creates Calendar events independently.

#### Hours Formatting Examples

The `round_hours` setting controls how task durations are rounded. Decimal places are automatic:

```yaml
# Example 1: Round to 30 minutes (default)
round_hours: 0.5
# 2h 12m → 2,0 hours (2h 00m) - 1 decimal
# 2h 38m → 2,5 hours (2h 30m) - 1 decimal
# 2h 52m → 3,0 hours (3h 00m) - 1 decimal

# Example 2: Round to 15 minutes  
round_hours: 0.25
# 2h 12m → 2,25 hours (2h 15m) - 2 decimals
# 2h 38m → 2,50 hours (2h 30m) - 2 decimals
# 2h 52m → 2,75 hours (2h 45m) - 2 decimals

# Example 3: Round to full hour
round_hours: 1.0
# 2h 12m → 2 hours - 0 decimals
# 2h 38m → 3 hours - 0 decimals
```

**Note:** Uses comma (`,`) as decimal separator for European format.

### Project-Based Workflow

Once configured, you can organize your work by project:

```bash
# Start tasks with project categorization
drudge start "API refactoring" --project Backend
drudge start "Button animations" --project Frontend

# Tasks are tracked with their projects
drudge list
# Output shows: "API refactoring [Backend]" and "Button animations [Frontend]"

# End tasks (project info is preserved)
drudge end "API refactoring"
# Output: 🏁 Completed 'API refactoring' [Backend] (2h 30m)
```

### Haunts Sync

When enabled, drudge can sync completed tasks to Google Calendar via Haunts:

```bash
# Manual sync (when sync_mode: manual)
drudge daily --sync

# View what will be synced
drudge daily
# Shows completed tasks with their projects and durations
```

**Note**: Haunts integration requires the [Haunts](https://github.com/yourusername/haunts) package to be installed and configured.

## 📖 Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| **Task Management** | | |
| `drudge start "Name"` | 🚀 Start a new task (auto-ends previous) | `drudge start "Bug fix #123"` |
| `drudge start` | 🚀 Start anonymous work session | `drudge start` |
| `drudge start --parallel` | 🚀 Start without ending active tasks | `drudge start "Review" --parallel` |
| `drudge start --project NAME` | 🚀 Start with project categorization | `drudge start "API work" --project Backend` |
| `drudge start --time HH:MM` | 🚀 Start at specific time | `drudge start "Meeting" --time 09:30` |
| `drudge end "Name"` | 🏁 End a specific task | `drudge end "Bug fix #123"` |
| `drudge end` | 🏁 End ALL active tasks (paused remain) | `drudge end` |
| `drudge end --all` | 🏁 **NEW** End active AND paused tasks | `drudge end --all` |
| `drudge end --time HH:MM` | 🏁 End at specific time | `drudge end "Meeting" --time 17:30` |
| `drudge pause "Name"` | ⏸️ Pause an active task | `drudge pause "Task"` |
| `drudge resume "Name"` | ▶️ Resume a paused task | `drudge resume "Task"` |
| **Cleaning & Maintenance** | | |
| `drudge clean YYYY-MM-DD` | 🗑️ **NEW** Clean all entries for date | `drudge clean 2025-10-03` |
| `drudge clean "Task"` | 🗑️ **NEW** Clean task (all dates) | `drudge clean "Bug fix"` |
| `drudge clean "Task" --date` | 🗑️ **NEW** Clean task for specific date | `drudge clean "Meeting" -d 2025-10-03` |
| `drudge clean --all` | 🗑️ **NEW** Clean ALL entries (confirm) | `drudge clean --all` |
| **Viewing & Reporting** | | |
| `drudge list` | 📋 Show active, paused, completed | `drudge list` |
| `drudge list --date YYYY-MM-DD` | 📋 List entries for date | `drudge list --date 2025-10-03` |
| `drudge list --task "keyword"` | 📋 Filter by task name | `drudge list --task "bug"` |
| `drudge list --limit N` | 📋 Limit results | `drudge list --limit 10` |
| `drudge recent` | 📝 Recent tasks (full details) | `drudge recent` |
| `drudge recent --limit N` | 📝 Show N recent tasks | `drudge recent --limit 10` |
| `drudge daily` | 📅 Today's summary | `drudge daily` |
| `drudge daily --date YYYY-MM-DD` | 📅 Specific date summary | `drudge daily --date 2025-10-03` |
| **Help & Info** | | |
| `drudge --help` | ❓ **IMPROVED** Main help | `drudge --help` |
| `drudge COMMAND --help` | ❓ **IMPROVED** Command help | `drudge start --help` |
| **Configuration** | | |
| `drudge config` | ⚙️ Show configuration help | `drudge config` |
| `drudge config --setup` | ⚙️ **NEW** Interactive setup wizard | `drudge config --setup` |
| `drudge config --show` | ⚙️ **NEW** Display current config | `drudge config --show` |
| `drudge config --edit` | ⚙️ **NEW** Edit config file | `drudge config --edit` |
| `drudge version` | 📦 Show version | `drudge version` |

## 💡 Usage Examples

### Basic Task Tracking

```bash
# Start a task
$ drudge start "Fix bug #123"
🚀 Started 'Fix bug #123' at 2025-10-04 10:00:00

# End it
$ drudge end "Fix bug #123"
🏁 Completed 'Fix bug #123' at 2025-10-04 12:30:00 (Duration: 02:30:00)
```

### Anonymous Work Session

```bash
# Don't know what you're working on yet?
$ drudge start
💡 Starting anonymous work session

# Name it later (converts anonymous → named)
$ drudge start "Research and planning"
✏️ Renamed anonymous work to 'Research and planning'
```

### Parallel Tasks

```bash
# Work on multiple tasks simultaneously
$ drudge start "Backend API"
$ drudge start "Code review" --parallel  # Keeps Backend API running

$ drudge list
🔥 ACTIVE TASKS:
  • Backend API (Running: 01:00:00)
  • Code review (Running: 00:15:00)

# End specific task
$ drudge end "Code review"
🏁 Completed 'Code review' (Duration: 00:30:00)
```

### Pause and Resume

```bash
# Working on a task
$ drudge start "Important project"

# Lunch break
$ drudge pause "Important project"
⏸️ Paused 'Important project'

# Back from lunch
$ drudge resume "Important project"
▶️ Resumed 'Important project'

# Finish up
$ drudge end "Important project"
🏁 Completed 'Important project' (Duration: 03:30:00)
```

### Enhanced End Command (v2.1.0)

```bash
# Create test scenario
$ drudge start "Active Task"
$ drudge start "Another Task" --parallel
$ drudge pause "Active Task"

$ drudge list
🔥 ACTIVE TASKS:
  • Another Task (Running: 00:05:00)

⏸️  PAUSED TASKS:
  • Active Task

# End only active tasks (DEFAULT behavior)
$ drudge end
✅ Ended 1 task(s) successfully  # Only "Another Task" ended

$ drudge list
⏸️  PAUSED TASKS:
  • Active Task  # Paused task remains!

# End ALL tasks including paused (NEW --all flag)
$ drudge end --all
▶️ Resumed 'Active Task'
🏁 Completed 'Active Task'
✅ Ended 1 task(s) successfully
```

### Clean Command (v2.1.0)

```bash
# Clean all entries for a specific date
$ drudge clean 2025-10-03
✅ Cleaned 15 entries for 2025-10-03
💾 Backup created for safety

# Clean all entries for a task (across all dates)
$ drudge clean "Bug fix #123"
✅ Cleaned 3 entries for task 'Bug fix #123'
💾 Backup created for safety

# Clean task entries for specific date only
$ drudge clean "Meeting" --date 2025-10-03
✅ Cleaned 1 entries for task 'Meeting' on 2025-10-03
💾 Backup created for safety

# Clean everything (with confirmation)
$ drudge clean --all
⚠️  This will clean ALL worklog entries!
Are you sure you want to continue? [y/N]: y
✅ Cleaned 50 entries and 10 daily files
💾 Backup created for safety
```

### Custom Time Entry

```bash
# Forgot to track? Backdate it
$ drudge start "Morning standup" --time 09:00
🚀 Started 'Morning standup' at 2025-10-04 09:00:00

$ drudge end "Morning standup" --time 09:30
🏁 Completed 'Morning standup' (Duration: 00:30:00)
```

### Daily Reporting

```bash
# View today's summary
$ drudge daily
📅 Daily Summary for 2025-10-04
📊 Total: 5 tasks, 7h 30m

  • Fix bug #123: 2h 30m
  • Code review: 1h 00m
  • Morning standup: 0h 30m
  • Documentation: 2h 00m
  • Backend API: 1h 30m

# View specific date
$ drudge daily --date 2025-10-03
```

### Project-Based Workflow (v2.1.1+)

```bash
# First, set up configuration with projects
$ drudge config --setup
# Follow the wizard to configure projects

# Start tasks with project categorization
$ drudge start "Implement login API" --project Backend
🚀 Started 'Implement login API' [Backend] at 2025-10-04 10:00:00

$ drudge start "Fix responsive design" --project Frontend --parallel
🚀 Started 'Fix responsive design' [Frontend] at 2025-10-04 10:30:00

# List shows projects
$ drudge list
🔥 ACTIVE TASKS:
  • Implement login API [Backend] (Running: 02:00:00)
  • Fix responsive design [Frontend] (Running: 01:30:00)

# End tasks (project info is preserved)
$ drudge end "Implement login API"
🏁 Completed 'Implement login API' [Backend] (Duration: 02:00:00)

$ drudge end "Fix responsive design"
🏁 Completed 'Fix responsive design' [Frontend] (Duration: 01:30:00)

# Daily summary shows projects
$ drudge daily
📅 Daily Summary for 2025-10-04
📊 Total: 2 tasks, 3h 30m

  • Implement login API [Backend]: 2h 00m
  • Fix responsive design [Frontend]: 1h 30m

# Sync to Google Calendar (with Haunts integration)
$ drudge daily --sync
✅ Synced 2 tasks to Google Calendar
```

## 📊 Google Sheets Integration

Drudge can sync your work tasks to Google Sheets in a **haunts-compatible format**. This allows you to:
- Keep a time-tracking spreadsheet
- Sync to Google Calendar (if using [haunts](https://github.com/keul/haunts))
- Share work reports with your team

### Quick Setup

1. **Create or use existing Google Sheet**
2. **Run config wizard:**
   ```bash
   drudge config --setup
   # Enable Google Sheets sync
   # Enter your Sheet Document ID
   # Configure formatting preferences
   ```

3. **Sync your tasks:**
   ```bash
   drudge sync              # Sync all entries
   drudge sync --daily      # Sync today's entries
   drudge sync --monthly    # Sync current month
   drudge daily --sync      # Alias for --daily
   ```

### Sheet Structure

Your Google Spreadsheet should have:

**1. Config Sheet** (name: `config`)
- Maps project names to Calendar IDs (optional for drudge, required for haunts)

**2. Monthly Sheets** (names: `January`, `February`, `March`, etc.)
- Auto-created based on task dates
- Contains your task entries

**Monthly Sheet Columns:**

| Column | Name | Description | Example |
|--------|------|-------------|---------|
| A | Date | Task date | `04/10/2025` |
| B | Start time | Task start time | `09:30` |
| C | Project | Project category | `Backend` |
| D | Activity | Task description | `Implement login API` |
| E | Details | Additional notes | `Added JWT auth` |
| F | Spent | Duration (decimal hours) | `2,5` |
| G | Event id | Calendar event ID (filled by haunts) | - |
| H | Link | Calendar event link (filled by haunts) | - |
| I | Action | Sync control (used by haunts) | - |

### Example Data

**Task in drudge:**
```bash
drudge start "Implement login API" --project Backend
# ... work for 2h 30m ...
drudge end "Implement login API"
```

**Synced to Google Sheet (October tab):**
```
| Date       | Start | Project | Activity             | Spent |
|------------|-------|---------|---------------------|-------|
| 04/10/2025 | 09:00 | Backend | Implement login API | 2,5   |
```

### Hours Formatting

Configure how hours are formatted in the sheet:

```yaml
google_sheets:
  hours_decimal: 1      # Decimal places (0, 1, or 2)
  round_hours: 0.25     # Round to 15min (0.25), 30min (0.5), or hour (1.0)
```

**Examples:**
- Task: 2h 47m
- `hours_decimal: 1, round_hours: 0.25` → `2,75` (2h 45m)
- `hours_decimal: 2, round_hours: 0.5` → `2,50` (2h 30m)  
- `hours_decimal: 0, round_hours: 1.0` → `3` (3h)

### Haunts Integration (Optional)

If you use **haunts** for Calendar sync:

1. **Drudge** → Writes tasks to Google Sheet
2. **Haunts** → Reads sheet and creates Calendar events
3. **Haunts** → Fills `Event id` and `Link` columns

**Without haunts:**
- You still get a time-tracking spreadsheet
- No automatic calendar sync
- Perfect for manual reporting

### Authentication Setup

To use Google Sheets sync, you need:

1. **Google Cloud Project** with Sheets API enabled
2. **OAuth 2.0 credentials** or service account
3. **Credentials file** at `~/.worklog/credentials.json`

See [Google Sheets API Quickstart](https://developers.google.com/sheets/api/quickstart/python) for detailed setup.

### Complete Documentation

For detailed sheet structure, column specifications, and setup guides, see:
- 📄 [Google Sheets Structure Documentation](docs/GOOGLE_SHEETS_STRUCTURE.md)

## 🏗️ Architecture

### Package Structure

```
src/worklog/
├── __init__.py          # Package initialization
├── __main__.py          # Entry point
├── models.py            # Data models (TaskEntry, PausedTask, WorkLogData)
├── config.py            # Configuration management
├── validators.py        # Input validation
├── managers/            # Business logic
│   ├── worklog.py       # Core WorkLog class
│   ├── backup.py        # Backup management
│   └── daily_file.py    # Daily file operations
├── cli/                 # Command-line interface
│   └── commands.py      # Typer commands
└── utils/               # Utilities
    └── decorators.py    # Common decorators
```

### Data Storage

```
~/.worklog/
├── worklog.json         # Complete task database (JSON)
├── worklog.log          # Application logs
├── 2025-10-01.txt      # Human-readable daily logs
├── 2025-10-02.txt
├── 2025-10-03.txt
└── daily/              # Backup directory
    ├── 2025-10-01.txt
    └── 2025-10-02.txt
```

### Daily File Format

```
2025-10-04 09:00:00 Morning standup (00:30:00)
2025-10-04 10:00:00 Fix bug #123 (02:30:00)
2025-10-04 14:00:00 Backend API [ACTIVE]
2025-10-04 15:00:00 Code review [PAUSED]
```

## 🔄 Version History

### Version 2.1.0 (Current - October 4, 2025)

**New Features:**
- ✨ **Enhanced end command**: `--all` flag to end both active and paused tasks
- ✨ **Clean command**: Erase worklog entries by date, task, or all (with backups)
- ✨ **Improved help**: Native Typer `--help` integration (removed custom help command)

**Improvements:**
- 🔧 End command: `drudge end` keeps paused tasks, `drudge end --all` ends everything
- 🛡️ Clean safety: Automatic backups, confirmation for --all, smart daily file rebuild
- 📚 All 39 test cases passing

### Version 2.0.2

**New Features:**
- Anonymous work sessions
- Parallel task mode
- Optimized list command
- Enhanced recent command

### Version 2.0.1

**Major Refactoring:**
- Complete architectural overhaul
- Typer CLI framework with Rich formatting
- Professional package structure
- 28 comprehensive test cases

### Version 1.0

- Initial release with basic task tracking

## 🧪 Testing

### Run Tests

```bash
# Run all tests
python3.10 -m pytest test_worklog_updated.py -v

# Run specific test class
python3.10 -m pytest test_worklog_updated.py::TestNewFeatures -v
```

### Test Coverage
- **39 comprehensive test cases**
- 100% pass rate on Python 3.10 and 3.13
- Core features: Start, end, pause, resume
- New features: Anonymous tasks, parallel mode, clean command
- Edge cases and error handling

## 🛠️ Development

### Build Package

```bash
# Build distribution
python3.10 -m build

# Check distribution
twine check dist/*
```

### Publish to PyPI

```bash
# Upload to PyPI
twine upload dist/*
```

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

## 🔗 Links

- **GitHub**: [github.com/Trik16/drudge](https://github.com/Trik16/drudge)
- **PyPI**: [pypi.org/project/drudge-cli](https://pypi.org/project/drudge-cli/)
- **Changelog**: [CHANGELOG.md](https://github.com/Trik16/drudge/blob/main/CHANGELOG.md)
- **Release Notes**: [docs/RELEASE_2.1.0.md](https://github.com/Trik16/drudge/blob/main/docs/RELEASE_2.1.0.md)

## 🙏 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 💬 Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

**Built with ❤️ using Python, Typer, and Rich**

**Version 2.1.1** - Enhanced CLI with native help, powerful clean command, and improved task management
