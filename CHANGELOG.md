# Changelog

All notable changes to drudge-cli will be documented in this file.

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
- 39 comprehensive test cases (all passing)

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
