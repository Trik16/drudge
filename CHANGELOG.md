# Changelog

All notable changes to drudge-cli will be documented in this file.

## [2.2.2] - 2025-12-03

### Fixed
- **Critical bug**: `get_worklog()` was creating config with defaults instead of loading from YAML
- **Config now loaded correctly**: All commands now properly read `~/.worklog/config.yaml` settings
- **Template default changed**: `google_sheets.enabled` now defaults to `false` to avoid confusion

## [2.2.1] - 2025-12-03

### Added
- **Auto-generated config file**: `~/.worklog/config.yaml` is now automatically created from template on first run
- **`drudge config --show`**: New option to display full config.yaml content with syntax highlighting
- **Config file included in package**: `config.yaml.example` now bundled with pip installation

### Changed
- **`drudge config`**: Now shows config summary including Google Sheets status and file location
- **README updated**: Removed references to non-existent `--setup` and `--edit` options

### Fixed
- **Config file creation**: Previously config.yaml was never created, only loaded if it existed

## [2.2.0] - 2025-12-03

### Added

#### Enhanced `--time` Option with Date Support
- **Full datetime format**: `--time "YYYY-MM-DD HH:MM"` now supported on all time-related commands
- **Backward compatible**: Existing `--time HH:MM` format continues to work (uses today's date)
- **Available commands**: `start`, `end`, `pause`, `resume`
- **Centralized validation**: `WorkLogValidator.validate_datetime_format()` handles both formats

Examples:
```bash
drudge start "Meeting" --time "2025-12-10 14:00"
drudge end "Meeting" --time "2025-12-10 17:30"
```

#### Project/Category Support
- **`--project` / `-P` option**: Assign tasks to projects on start command
- **Project filtering**: Filter completed tasks by project in list command
- **Display enhancement**: Projects shown in parentheses for active and completed tasks
- **Backend support**: `TaskEntry.project` field and `active_task_projects` tracking

Examples:
```bash
drudge start "Fix bug" --project "Backend API"
drudge list --project "Backend"
```

#### Google Sheets Sync with Haunts-Compatible Format
- **`HauntsAdapter`**: New adapter in `src/worklog/sync/sheets.py` supporting three authentication methods:
  1. **Haunts OAuth**: Reuses existing haunts credentials from `~/.config/haunts/`
  2. **OAuth Token File**: Direct OAuth token JSON (with `refresh_token`)
  3. **Service Account**: Standard Google Service Account JSON (with `client_email`)

- **Configuration field `use_haunts_format`**: New boolean in `google_sheets` section:
  ```yaml
  google_sheets:
    enabled: true
    use_haunts_format: true  # true = haunts format, false = legacy gspread
    round_hours: 0.5
  ```

- **Dependency `google-api-python-client>=2.108.0`**: Added to base dependencies for direct Sheets API support

- **Optional dependency `haunts>=0.7.0`**: Available as `[sheets]` extra:
  ```bash
  pip install 'drudge-cli[sheets]'
  ```

#### Dev Environment Reorganization
- **`dev-env/` folder**: Docker test files moved to dedicated directory
- **Dynamic paths**: Scripts use config-based paths for credentials and sheet IDs
- **Included files**: `Dockerfile.test`, `test_haunts_sync.py`, `create_november_tasks.py`, `clear_november.py`, `check_headers.py`

#### Authentication Flow
```
GoogleSheetsSync(config, credentials_path)
│
├─ use_haunts_format=true (default)
│   ├─ credentials_path provided → OAuth Token or Service Account
│   └─ credentials_path=None + haunts installed → ~/.config/haunts/ OAuth
│
└─ use_haunts_format=false → Legacy gspread backend
```

#### Output Format (Haunts-Compatible)
| Column | Example | Description |
|--------|---------|-------------|
| A: Date | `18/11/2025` | DD/MM/YYYY format |
| B: Start time | `09:00` | HH:MM format |
| C: Spent | `2,5` | Hours with comma decimal |
| D: Project | `pippo` | Project name |
| E: Activity | `Setup dev...` | Task name |
| F: Details | | Empty (reserved) |
| G-J | | Reserved for haunts Calendar sync |

### Changed

#### `src/worklog/sync/sheets.py`
- **`GoogleSheetsSync.__init__`**: Removed `use_haunts` parameter, now reads from config
- **Column order fixed**: Correct haunts order (Date, Start time, Spent, Project, Activity, Details...)
- **Clear error messages**: Suggested solutions when initialization fails

#### `src/worklog/config.py`
- **`GoogleSheetsConfig.use_haunts_format`**: New field (default `True`)
- **YAML loader**: Ignores unknown fields for backward compatibility

#### `src/worklog/cli/commands.py`
- **`start` command**: Added `--project` / `-P` option
- **`list` command**: Added `--project` / `-P` filter option
- **All time commands**: Updated `--time` help to show both formats

#### `src/worklog/managers/worklog.py`
- **`list_entries()`**: Added `project_filter` parameter and project display
- **`_parse_custom_time()`**: Now handles full datetime format

#### Configuration
- **`sheet_document_id`**: Single source of truth at root level
- Removed obsolete fields: `google_sheets.document_id`, `google_sheets.credentials_file`

### Fixed
- **Column order**: Data now written in correct haunts column order
- **`TaskEntry.description`**: Removed reference to non-existent field
- **Document ID duplication**: Consolidated to single `sheet_document_id` field

### Test Coverage
- **117 comprehensive test cases** (all passing)
- New tests for `--time` with date format (3 tests)
- New tests for `--project` option (4 tests)
- New tests for datetime validation (5 tests)
- Unit tests use `use_haunts_format=false` to avoid credential dependency
- Integration tests with real Google Sheets sync verified

## [2.1.1] - 2025-10-04

### Fixed
- Updated README.md with corrected GitHub links for CHANGELOG and release notes
- Links now properly point to GitHub repository instead of relative paths

### Changed
- Version command now imports `__version__` from `__init__.py` instead of hardcoding it
- Single source of truth for version number across the codebase

## [2.1.0] - 2025-10-04

### Added
- **Enhanced end command**: New `--all` flag to end both active and paused tasks
  - `drudge end` (no args) - Ends only active tasks, paused tasks remain
  - `drudge end --all` - Ends all tasks including paused (resumes them first)
  
- **Clean command**: New command to erase worklog entries with automatic backup
  - `drudge clean YYYY-MM-DD` - Clean all entries for a specific date
  - `drudge clean "Task name"` - Clean all entries for a task across all dates
  - `drudge clean "Task" --date YYYY-MM-DD` - Clean task entries for specific date only
  - `drudge clean --all` - Clean ALL worklog entries (with confirmation prompt)
  
- **Improved help system**: Removed custom help command, use native Typer `--help`
  - `drudge --help` - Main help
  - `drudge COMMAND --help` - Command-specific help

### Changed
- End command behavior improved for paused tasks
- Clean command creates automatic backups before any deletion
- Clean command rebuilds daily files when partially cleaning entries

### Fixed
- Format entry signature in clean_by_task method
- Daily file rebuild logic when removing specific task entries

## [2.0.2] - 2025-10-03

### Added
- Anonymous work sessions (start without task name)
- Seamless anonymous-to-named task conversion
- End all active tasks with single command
- Parallel mode for concurrent tasks (`--parallel` flag)
- Optimized list command (active-first, then last 2 recent)
- Enhanced recent command with full entry details

### Changed
- Better single-task mode (auto-ends previous task by default)
- Custom time options verified for start/end commands
- Unified list command (combines status + history in one command)
- Enhanced documentation and examples

### Test Coverage
- 47 comprehensive test cases (all passing)

## [2.0.1] - 2025-10-01

### Changed
- Complete architectural overhaul with modern Python patterns
- Typer CLI framework with Rich formatting
- Professional package structure under `src/worklog/`
- Centralized validation and configuration management

### Test Coverage
- 28 comprehensive test cases

## [1.0.0] - Initial Release

### Added
- Initial release with basic task tracking
- Argparse-based CLI
- Simple JSON storage
