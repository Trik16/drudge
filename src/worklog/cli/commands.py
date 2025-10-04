"""
CLI commands module for the WorkLog application.

This module contains all Typer CLI command definitions and integrates
with the core WorkLog functionality through the managers package.
"""
import logging
from typing import Optional
from pathlib import Path

import typer
from rich.console import Console

from ..managers.worklog import WorkLog
from ..config import WorkLogConfig
from .. import __version__

# Initialize Rich console and logger
console = Console()
logger = logging.getLogger(__name__)

# Create Typer application
app = typer.Typer(
    name="drudge",
    help="🚀 Drudge CLI - A comprehensive work time tracking tool with task management, time tracking, and reporting features.",
    no_args_is_help=True,
    rich_markup_mode="rich",
    add_completion=True,
    pretty_exceptions_show_locals=False
)

# Global WorkLog instance - initialized on first command
_worklog_instance: Optional[WorkLog] = None


def get_worklog() -> WorkLog:
    """
    Get or create the global WorkLog instance.
    
    Returns:
        WorkLog: Configured WorkLog instance
    """
    global _worklog_instance
    if _worklog_instance is None:
        config = WorkLogConfig()
        _worklog_instance = WorkLog(config=config)
    return _worklog_instance


# ============================================================================
# Task Management Commands
# ============================================================================

@app.command()
def start(
    task_name: Optional[str] = typer.Argument(None, help="Name of the task to start (anonymous if omitted)"),
    time: Optional[str] = typer.Option(None, "--time", "-t", help="Custom start time in HH:MM format"),
    force: bool = typer.Option(False, "--force", "-f", help="Force start by ending active tasks"),
    parallel: bool = typer.Option(False, "--parallel", "-p", help="Allow parallel tasks (don't auto-end active tasks)")
) -> None:
    """
    🚀 Start a new task or resume a paused one.
    
    By default, starting a new task ends any active tasks (single-task mode).
    Use --parallel to work on multiple tasks simultaneously.
    Omit task name to start anonymous work session.
    
    Examples:
        drudge start "Fix bug #123"
        drudge start                    # Anonymous work
        drudge start "Review PR" --time 09:30
        drudge start "Meeting" --parallel
        drudge start "Task" --force     # End active tasks first
    """
    worklog = get_worklog()
    
    # Handle modes:
    # - parallel=True: Allow concurrent tasks (don't auto-end)
    # - parallel=False (default): Single-task mode (auto-end active tasks)
    # force parameter is respected in both modes for explicit auto-ending
    auto_end_mode = not parallel  # Single-task mode auto-ends
    success = worklog.start_task(task_name, custom_time=time, force=force or auto_end_mode, parallel=parallel)
    
    if not success:
        raise typer.Exit(1)


@app.command()
def end(
    task_name: Optional[str] = typer.Argument(None, help="Name of the task to end (omit to end all active tasks)"),
    time: Optional[str] = typer.Option(None, "--time", "-t", help="Custom end time in HH:MM format"),
    all: bool = typer.Option(False, "--all", "-a", help="End all active AND paused tasks")
) -> None:
    """
    🏁 End an active task and record completion.
    
    Omit task name to end all active tasks.
    Use --all to also end paused tasks (converting accumulated time to entries).
    
    Examples:
        drudge end "Fix bug #123"
        drudge end "Meeting" --time 17:30
        drudge end                          # End all active tasks
        drudge end --all                    # End all active AND paused tasks
    """
    worklog = get_worklog()
    
    # If --all flag is used, end all active AND paused tasks
    if all:
        worklog.end_all_tasks(custom_time=time, include_paused=True)
    # If no task name provided, end all active tasks
    elif task_name is None:
        worklog.end_all_tasks(custom_time=time, include_paused=False)
    # End specific task
    else:
        success = worklog.end_task(task_name, custom_time=time)
        if not success:
            raise typer.Exit(1)


@app.command()
def pause(
    task_name: str = typer.Argument(..., help="Name of the task to pause"),
    time: Optional[str] = typer.Option(None, "--time", "-t", help="Custom pause time in HH:MM format")
) -> None:
    """
    ⏸️ Pause an active task for later resumption.
    
    Examples:
        worklog pause "Fix bug #123"
        worklog pause "Review PR" --time 12:00
    """
    worklog = get_worklog()
    success = worklog.pause_task(task_name, custom_time=time)
    
    if not success:
        raise typer.Exit(1)


@app.command()
def resume(
    task_name: str = typer.Argument(..., help="Name of the task to resume"),
    time: Optional[str] = typer.Option(None, "--time", "-t", help="Custom resume time in HH:MM format")
) -> None:
    """
    ▶️ Resume a paused task.
    
    Examples:
        worklog resume "Fix bug #123"
        worklog resume "Review PR" --time 13:00
    """
    worklog = get_worklog()
    success = worklog.resume_task(task_name, custom_time=time)
    
    if not success:
        raise typer.Exit(1)


# ============================================================================
# Status and Information Commands
# ============================================================================

@app.command()
def recent(
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of tasks shown")
) -> None:
    """
    📝 List recent tasks for quick reference.
    
    Example:
        worklog recent --limit 10
    """
    worklog = get_worklog()
    worklog.list_recent_tasks(limit=limit)


@app.command()
def list(
    date: Optional[str] = typer.Option(None, "--date", "-d", help="Filter by date (YYYY-MM-DD)"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of entries"),
    task: Optional[str] = typer.Option(None, "--task", "-t", help="Filter by task name")
) -> None:
    """
    📋 Show work status: active tasks, paused tasks, and completed entries.
    
    Without filters: Shows current status (active/paused tasks + today's count)
    With filters: Shows filtered completed entries
    
    Examples:
        drudge list                      # Show current status
        drudge list --date 2025-01-15    # Show tasks from specific date
        drudge list --task "bug" --limit 5
    """
    worklog = get_worklog()
    worklog.list_entries(date=date, limit=limit, task_filter=task)


@app.command()
def daily(
    date: Optional[str] = typer.Option(None, "--date", "-d", help="Date for summary (YYYY-MM-DD)")
) -> None:
    """
    📅 Show daily work summary with time totals.
    
    Examples:
        drudge daily
        drudge daily --date 2025-01-15
    """
    worklog = get_worklog()
    worklog.show_daily_summary(date=date)


@app.command()
def clean(
    target: Optional[str] = typer.Argument(None, help="Date (YYYY-MM-DD) or task name to clean"),
    date: Optional[str] = typer.Option(None, "--date", "-d", help="Filter by date when cleaning a task"),
    all: bool = typer.Option(False, "--all", "-a", help="Clean all worklog entries")
) -> None:
    """
    🗑️ Clean worklog entries by date, task, or all.
    
    Creates a backup before cleaning for safety.
    
    Examples:
        drudge clean 2025-10-03              # Clean all entries for a date
        drudge clean "Bug fix"               # Clean all entries for a task
        drudge clean "Meeting" --date 2025-10-03  # Clean task entries for specific date
        drudge clean --all                   # Clean all worklog entries
    """
    worklog = get_worklog()
    
    # Clean all entries
    if all:
        if target is not None:
            console.print("❌ Cannot specify a target when using --all", style="red")
            raise typer.Exit(1)
        
        # Confirm before cleaning all
        console.print("⚠️  [yellow]This will clean ALL worklog entries![/yellow]")
        confirm = typer.confirm("Are you sure you want to continue?")
        if not confirm:
            console.print("❌ Operation cancelled", style="dim")
            raise typer.Exit(0)
        
        worklog.clean_all()
        return
    
    # No target specified
    if target is None:
        console.print("❌ Please specify a date, task name, or use --all", style="red")
        raise typer.Exit(1)
    
    # Check if target is a date (YYYY-MM-DD format)
    import re
    date_pattern = r'^\d{4}-\d{2}-\d{2}$'
    
    if re.match(date_pattern, target):
        # Clean by date
        if date is not None:
            console.print("❌ Cannot use --date when target is already a date", style="red")
            raise typer.Exit(1)
        worklog.clean_by_date(target)
    else:
        # Clean by task name
        worklog.clean_by_task(target, date=date)


# ============================================================================
# Configuration and Utility Commands
# ============================================================================

@app.command()
def config() -> None:
    """
    ⚙️ Show current configuration settings.
    """
    worklog = get_worklog()
    console.print("⚙️ Drudge CLI Configuration:", style="bold")
    console.print(f"📁 Data directory: {worklog.worklog_dir}")
    console.print(f"📄 Data file: {worklog.worklog_file}")
    console.print(f"🕐 Display format: {worklog.config.display_time_format}")
    console.print(f"📋 Max recent tasks: {worklog.config.max_recent_tasks}")
    console.print(f"💾 Max backups: {worklog.config.max_backups}")


@app.command()
def version() -> None:
    """
    📦 Show Drudge CLI version information.
    """
    console.print("🚀 Drudge CLI", style="bold blue")
    console.print(f"Version: {__version__} (Enhanced CLI)")
    console.print("A comprehensive work time tracking and task management tool")


# ============================================================================
# Error Handling and Main Entry
# ============================================================================

def setup_logging(verbose: bool = False) -> None:
    """
    Setup logging configuration for the CLI.
    
    Args:
        verbose: Enable debug logging if True
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Path.home() / '.worklog' / 'worklog.log'),
            logging.StreamHandler() if verbose else logging.NullHandler()
        ]
    )


def main() -> None:
    """
    Main entry point for the CLI application.
    
    Handles global exception catching and logging setup.
    """
    try:
        # Setup basic logging
        setup_logging()
        
        # Run the Typer app
        app()
        
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!", style="yellow")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}", style="red")
        logger.exception("Unexpected error in CLI")
        raise typer.Exit(1)


if __name__ == "__main__":
    main()