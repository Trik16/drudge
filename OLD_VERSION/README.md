# OLD_VERSION - Legacy Files

This directory contains the pre-refactoring version of the WorkLog CLI tool.

## Files

- **worklog.py** - The final monolithic version before the package refactor (72,999 lines)
- **worklog_original.py** - Earlier version backup
- **worklog_argparse_backup.py** - Version using argparse instead of Typer
- **test_*.py** - Old test files for the monolithic version

## Note

These files are kept for reference and historical purposes. The current version of Drudge CLI is in the `src/worklog/` package.

**Do not use these files directly.** Use the new package-based version instead:

```bash
python3 -m src.worklog --help
```

Or with the alias:

```bash
drudge --help
```

## Migration Date

These files were archived on October 3, 2025, after completing the comprehensive package refactoring (Point 2 of the development roadmap).
