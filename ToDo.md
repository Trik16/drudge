# Drudge CLI - Next Steps Todo List

## ✅ Completed Tasks

### Version 2.1.0 (October 4, 2025) ✅ **RELEASED**
- [x] **Enhanced CLI Features**
  - [x] Native help system integration (removed custom help command, using Typer's --help)
  - [x] Enhanced end command with `--all` flag to end active AND paused tasks
  - [x] Clean command implementation for worklog management:
    - `drudge clean YYYY-MM-DD` - Clean all entries for a date
    - `drudge clean "Task"` - Clean all entries for a task
    - `drudge clean "Task" --date YYYY-MM-DD` - Clean task for specific date
    - `drudge clean --all` - Clean all entries (with confirmation)
  - [x] Automatic backups before cleaning operations
  - [x] Smart daily file rebuilding for partial cleaning
  - [x] All 39 test cases passing

- [x] **Documentation & Release**
  - [x] Updated README.md with v2.1.0 features
  - [x] Created CHANGELOG.md for version history
  - [x] Created docs/RELEASE_2.1.0.md with detailed release notes
  - [x] Version bumped to 2.1.0 in all files (pyproject.toml, __init__.py, commands.py)

- [x] **CI/CD & Automation**
  - [x] GitHub Actions workflow for automated testing (test.yml)
  - [x] GitHub Actions workflow for PyPI publishing on tags (publish.yml)
  - [x] PyPI Trusted Publishing configuration (no API tokens needed)
  - [x] Created setup guides (GITHUB_ACTIONS_SETUP.md, GITHUB_ACTIONS_QUICKSTART.md)

- [x] **2. Folder and file refactor**
  - [x] Reorganized project structure into proper Python package with src/worklog/
  - [x] Split worklog.py into multiple modules with logical separation:
    - `models.py`: Data models (TaskEntry, PausedTask, WorkLogData)
    - `config.py`: Configuration management (WorkLogConfig)
    - `validators.py`: Centralized validation logic
    - `managers/`: Business logic (worklog.py, backup.py, daily_file.py)
    - `cli/`: Command-line interface (commands.py)
    - `utils/`: Utility functions (decorators.py)
  - [x] Implemented proper `__main__.py` and `__init__.py` structure
  - [x] All tests passing with new structure
  - [x] README updated with package architecture documentation

- [x] **1. Pip/PyPI publishing setup**
  - [x] Created pyproject.toml with proper metadata and dependencies
  - [x] Package name: `drudge-cli` (on PyPI)
  - [x] Command name: `drudge` (console script entry point)
  - [x] GitHub repository: https://github.com/Trik16/drudge
  - [x] Automated PyPI publishing via GitHub Actions
  - [x] Version 2.1.0 ready for release

## 🚀 Immediate Next Steps (Foundation)

- [ ] **Test Infrastructure Refactoring**
  - Unify test file structure and workflow refactor
  - Create a reusable GitHub Actions workflow for running all tests in the `tests/` folder
  - Create 2 separate workflows that call/reuse this test action:
    - One for continuous integration (on push/PR)
    - One for release validation (on tag creation)
  - Move all test files to a dedicated `tests/` directory
  - Ensure consistent test naming and organization

- [ ] **3. Configuration file support**
  - Add YAML/TOML configuration file support for persistent settings and user preferences
  - Allow customization of directories, formats, and default behaviors
  - Example: `~/.worklog/config.toml` or `~/.drudgerc`

## 🎯 Version 2.2.0 Planning (Future Release)

### Core Feature Extensions
- [ ] **4. Project/Category Support**
  - Add project grouping functionality to organize tasks by project or category with filtering and reporting
  - Enable task categorization and project-based time tracking
  - Example: `drudge start "Fix bug" --project "Backend API"`

- [ ] **5. Time Goals feature**
  - Implement daily/weekly time targets with progress tracking and notifications when goals are met
  - Add goal visualization and achievement tracking

- [ ] **6. Enhanced Reports generation**
  - Create detailed time reports with charts, summaries, and various output formats (console tables, markdown)
  - Include productivity metrics and time distribution analysis

- [ ] **7. Export/Import capabilities**
  - Add CSV, JSON, PDF export functionality and import from other time tracking tools
  - Support for common time tracking formats (Toggl, RescueTime, etc.)

## 🖥️ Desktop UI Development (drudge-ui)

### Architecture & Setup
- [ ] **1. Monorepo restructuring**
  - [ ] Reorganize repo to support two separate packages: `drudge-cli` and `drudge-ui`
  - [ ] Create `cli/` and `ui/` directories with independent package configurations
  - [ ] Update GitHub Actions for separate CI/CD pipelines
  - [ ] Maintain shared documentation and version coordination

- [ ] **2. Tauri UI framework setup**
  - [ ] Initialize Tauri project in `ui/` directory
  - [ ] Set up Rust toolchain and Tauri CLI
  - [ ] Configure Python bridge for calling drudge-cli commands
  - [ ] Create basic window and app structure

- [ ] **3. Frontend development (HTML/CSS/Vanilla JS)**
  - [ ] Design clean, minimal UI for visualizing CLI commands
  - [ ] Implement views:
    - **List view**: Display active, paused, and recent tasks
    - **Daily view**: Show today's task timeline and total hours
    - **Recent view**: Browse recent task history with filtering
  - [ ] Add basic styling with modern CSS (flexbox/grid)
  - [ ] Implement responsive layout for different window sizes

- [ ] **4. Python-Tauri bridge implementation**
  - [ ] Create Tauri commands to invoke drudge-cli operations
  - [ ] Implement IPC (Inter-Process Communication) layer
  - [ ] Handle CLI output parsing and display in UI
  - [ ] Add error handling and user feedback

- [ ] **5. UI package configuration**
  - [ ] Set up `pyproject.toml` for drudge-ui package
  - [ ] Configure PyPI publishing for developers (`pip install drudge-ui`)
  - [ ] Create installers for end users (.exe, .deb, .dmg)
  - [ ] Add GitHub Actions workflow for building cross-platform releases

- [ ] **6. Testing & Documentation**
  - [ ] Write UI-specific tests
  - [ ] Create drudge-ui README with installation instructions
  - [ ] Add screenshots and usage examples
  - [ ] Document UI architecture and development setup

**UI Tech Stack:**
- **Framework**: Tauri (lightweight, cross-platform)
- **Frontend**: HTML + CSS + Vanilla JavaScript (no complex frameworks)
- **Backend Bridge**: Python calling drudge-cli commands
- **Target Platforms**: Linux, Windows, macOS
- **Package Size Goal**: < 10 MB installers

**Release Strategy:**
- `drudge-cli`: PyPI package (existing)
- `drudge-ui`: PyPI package + GitHub release installers

## 🔌 Integration & Advanced Features
- [ ] **8. API Integration framework**
  - [ ] Create extensible API integration system for Slack, Jira, GitHub with webhook support
  - [ ] Enable automatic task creation from external systems

- [ ] **9. Desktop Notifications**
  - [ ] Implement cross-platform desktop notifications for long-running tasks, time targets, and reminders
  - [ ] Smart break reminders and productivity alerts

- [ ] **10. Database backend option**
  - [ ] Optional SQLite backend for better performance with large datasets and advanced querying
  - [ ] Maintain JSON compatibility while offering enhanced performance

- [ ] **11. Web dashboard (haunts integration)**
  - [ ] Create web-based dashboard for visual time tracking, possibly integrating with haunts or similar frameworks
  - [ ] Real-time task monitoring and visual analytics

- [ ] **12. Advanced analytics**
  - [ ] Add productivity analytics, time patterns analysis, and insights generation
  - [ ] Machine learning insights for productivity optimization

## 📝 Implementation Notes
- At the end of each task: tests must be run, README and todo files updated
- Maintain backward compatibility throughout all refactoring
- Ensure comprehensive test coverage for all new features
- Update documentation with each major change

## 📊 Current Status Summary

**Version:** 2.1.0 (Released October 4, 2025)

**Package Status:**
- ✅ Published on PyPI as `drudge-cli`
- ✅ Console command: `drudge`
- ✅ GitHub: https://github.com/Trik16/drudge
- ✅ Automated CI/CD with GitHub Actions
- ✅ 39 comprehensive test cases (100% passing)

**Recent Achievements (v2.1.0):**
- Enhanced CLI with native help system
- New clean command for worklog management
- End command with --all flag for paused tasks
- Complete documentation and release notes
- Automated testing and publishing workflows

**Next Major Milestone:** Version 2.2.0 - Configuration file support & Project categorization
