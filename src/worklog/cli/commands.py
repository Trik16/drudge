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

# Initialize Rich console and logger
console = Console()
logger = logging.getLogger(__name__)

# Create Typer application
app = typer.Typer(
    name="drudge",
    help="Drudge CLI - A comprehensive work time tracking tool with task management, time tracking, and reporting features.",
    no_args_is_help=True,
    rich_markup_mode="rich"
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
    task_name: str = typer.Argument(..., help="Name of the task to start"),
    time: Optional[str] = typer.Option(None, "--time", "-t", help="Custom start time in HH:MM format"),
    force: bool = typer.Option(False, "--force", "-f", help="Force start by ending active tasks")
) -> None:
    """
    🚀 Start a new task or resume a paused one.
    
    Examples:
        worklog start "Fix bug #123"
        worklog start "Review PR" --time 09:30
        worklog start "Meeting" --force
    """
    worklog = get_worklog()
    success = worklog.start_task(task_name, custom_time=time, force=force)
    
    if not success:
        raise typer.Exit(1)


@app.command()
def end(
    task_name: str = typer.Argument(..., help="Name of the task to end"),
    time: Optional[str] = typer.Option(None, "--time", "-t", help="Custom end time in HH:MM format")
) -> None:
    """
    🏁 End an active task and record completion.
    
    Examples:
        worklog end "Fix bug #123"
        worklog end "Review PR" --time 17:30
    """
    worklog = get_worklog()
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
def status() -> None:
    """
    📊 Show current work status and active tasks.
    """
    worklog = get_worklog()
    worklog.show_status()


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
    📋 List completed task entries with optional filtering.
    
    Examples:
        worklog list
        worklog list --date 2025-01-15
        worklog list --task "bug" --limit 5
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
        worklog daily
        worklog daily --date 2025-01-15
    """
    worklog = get_worklog()
    worklog.show_daily_summary(date=date)


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
    console.print("Version: 2.0.0 (Refactored)")
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