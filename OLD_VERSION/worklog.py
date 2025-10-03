#!/usr/bin/env python3
"""
WorkLog CLI Tool - Modern Python Implementation

A comprehensive CLI tool for tracking work time on tasks with organized daily logs.
Built with Typer for modern CLI interface, type hints, and rich features.

Usage: worklog [TASK_NAME] [OPTIONS]

First run: Starts tracking time for a task
Second run: Ends the task and calculates duration

Features:
- Single-task mode by default with optional parallel mode
- Custom start times for backdating entries
- Pause/resume functionality
- Anonymous work sessions
- Clean daily logs with backup
- Rich console output with colors and formatting
"""

from __future__ import annotations

import json
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any, Union
from dataclasses import dataclass, field
from contextlib import contextmanager
from functools import wraps, lru_cache
import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

# Initialize rich console for beautiful output
console = Console()
app = typer.Typer(
    name="worklog",
    help="📝 Track work time on tasks with organized daily logs",
    add_completion=False,
    rich_markup_mode="rich"
)

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Default to WARNING to avoid spam
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TaskEntry:
    """
    Data class representing a single task entry.
    
    Attributes:
        task: Task name or identifier
        start_time: ISO timestamp when task started
        end_time: ISO timestamp when task ended (None if active)
        duration: Human-readable duration string (None if active)
    """
    task: str
    start_time: str
    end_time: Optional[str] = None
    duration: Optional[str] = None

@dataclass 
class PausedTask:
    """
    Data class representing a paused task with accumulated time.
    
    Attributes:
        task: Task name or identifier
        total_duration_so_far: Accumulated duration string
        last_paused_at: ISO timestamp when task was paused
    """
    task: str
    total_duration_so_far: str
    last_paused_at: str

@dataclass
class WorkLogData:
    """
    Data class for the complete worklog state.
    
    Attributes:
        entries: List of all task entries
        active_tasks: Dictionary mapping active task names to start times
        paused_tasks: List of paused task information
        recent_tasks: List of recently used task names
    """
    entries: List[TaskEntry] = field(default_factory=list)
    active_tasks: Dict[str, str] = field(default_factory=dict)
    paused_tasks: List[PausedTask] = field(default_factory=list)
    recent_tasks: List[str] = field(default_factory=list)

@dataclass
class WorkLogConfig:
    """
    Configuration settings for WorkLog with sensible defaults.
    
    Attributes:
        worklog_dir_name: Name of the worklog directory
        date_format: Date format string for parsing and display
        time_format: Time format string for parsing user input
        display_time_format: Format for displaying timestamps to users
        max_recent_tasks: Maximum number of recent tasks to remember
        backup_enabled: Whether to create backups before destructive operations
        auto_save: Whether to automatically save after each operation
    """
    worklog_dir_name: str = '.worklog'
    date_format: str = "%Y-%m-%d"
    time_format: str = "%H:%M"
    display_time_format: str = "%Y-%m-%d %H:%M:%S"
    max_recent_tasks: int = 10
    backup_enabled: bool = True
    auto_save: bool = True

class WorkLogValidator:
    """
    Centralized validation logic for WorkLog inputs.
    
    Provides consistent validation with clear error messages for
    dates, times, task names, and other user inputs.
    """
    
    @staticmethod
    def validate_date_format(date_str: str, config: WorkLogConfig = None) -> None:
        """
        Validate date string format.
        
        Args:
            date_str: Date string to validate
            config: Configuration with date format (optional)
            
        Raises:
            ValueError: If date format is invalid
        """
        if config is None:
            config = WorkLogConfig()
            
        try:
            datetime.strptime(date_str, config.date_format)
        except ValueError:
            raise ValueError(f"Invalid date format: '{date_str}'. Expected format: {config.date_format}")
    
    @staticmethod
    def validate_time_format(time_str: str, config: WorkLogConfig = None) -> tuple[int, int]:
        """
        Validate and parse time string format.
        
        Args:
            time_str: Time string in HH:MM format
            config: Configuration with time format (optional)
            
        Returns:
            tuple: (hours, minutes) as integers
            
        Raises:
            ValueError: If time format is invalid or values out of range
        """
        if config is None:
            config = WorkLogConfig()
            
        try:
            # Parse time components
            time_parts = time_str.split(':')
            if len(time_parts) != 2:
                raise ValueError("Time must contain exactly one colon")
            
            hours, minutes = int(time_parts[0]), int(time_parts[1])
            
            # Validate ranges with descriptive errors
            if not (0 <= hours <= 23):
                raise ValueError(f"Hours must be between 00-23, got {hours}")
            if not (0 <= minutes <= 59):
                raise ValueError(f"Minutes must be between 00-59, got {minutes}")
                
            return hours, minutes
            
        except (ValueError, IndexError) as e:
            if "invalid literal for int()" in str(e):
                raise ValueError(f"Invalid time format '{time_str}': Non-numeric values found")
            raise ValueError(f"Invalid time format '{time_str}': {e}")
    
    @staticmethod
    def validate_time_sequence(start_time: str, stop_time: str) -> None:
        """
        Validate that stop time is after start time.
        
        Args:
            start_time: Start time in HH:MM format
            stop_time: Stop time in HH:MM format
            
        Raises:
            ValueError: If stop time is not after start time
        """
        start_hours, start_minutes = WorkLogValidator.validate_time_format(start_time)
        stop_hours, stop_minutes = WorkLogValidator.validate_time_format(stop_time)
        
        start_total_minutes = start_hours * 60 + start_minutes
        stop_total_minutes = stop_hours * 60 + stop_minutes
        
        if stop_total_minutes <= start_total_minutes:
            raise ValueError(f"Stop time ({stop_time}) must be after start time ({start_time})")
    
    @staticmethod
    def validate_task_name(task_name: str) -> None:
        """
        Validate task name is not empty and doesn't contain problematic characters.
        
        Args:
            task_name: Task name to validate
            
        Raises:
            ValueError: If task name is invalid
        """
        if not task_name or not task_name.strip():
            raise ValueError("Task name cannot be empty")
        
        if len(task_name.strip()) > 100:
            raise ValueError("Task name cannot exceed 100 characters")
        
        # Check for problematic characters that could break file operations
        problematic_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in problematic_chars:
            if char in task_name:
                raise ValueError(f"Task name cannot contain '{char}' character")

class BackupManager:
    """
    Centralized backup creation and management for WorkLog data.
    
    Handles creation of comprehensive backups before destructive operations,
    ensuring data safety with consistent backup format and error handling.
    """
    
    @staticmethod
    def create_backup(
        backup_dir: Path,
        date_str: str,
        entries: List[TaskEntry],
        daily_file: Optional[Path] = None,
        config: Optional[WorkLogConfig] = None
    ) -> Path:
        """
        Create a comprehensive backup file for a specific date.
        
        Args:
            backup_dir: Directory to store the backup
            date_str: Date string for the backup
            entries: Task entries to backup
            daily_file: Optional daily file to include in backup
            config: Configuration for formatting
            
        Returns:
            Path: Path to the created backup file
            
        Raises:
            IOError: If backup creation fails
        """
        if config is None:
            config = WorkLogConfig()
            
        backup_file = backup_dir / f"{date_str}_backup.txt"
        backup_content = []
        
        try:
            # Add JSON entries to backup
            if entries:
                backup_content.extend([
                    "=== JSON Entries ===",
                    ""
                ])
                for entry in entries:
                    task = entry.task
                    start = WorkLog._format_display_time(entry.start_time)
                    if entry.end_time:
                        end = WorkLog._format_display_time(entry.end_time)
                        duration = entry.duration
                        backup_content.append(f"{start} - {end} {task} ({duration})")
                    else:
                        backup_content.append(f"{start} - ACTIVE {task}")
                backup_content.append("")
            
            # Add daily file content to backup
            if daily_file and daily_file.exists():
                backup_content.extend([
                    "=== Daily File Content ===",
                    ""
                ])
                try:
                    with open(daily_file, 'r', encoding='utf-8') as f:
                        backup_content.extend(line.rstrip() for line in f)
                except Exception as e:
                    backup_content.append(f"Error reading daily file: {e}")
            
            # Write backup file
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(backup_content))
                
            logger.info(f"Backup created: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise IOError(f"Backup creation failed: {e}")

class DailyFileManager:
    """
    Manages daily file operations with improved organization and error handling.
    
    Separates daily file concerns from the main WorkLog class, providing
    specialized methods for file manipulation, chronological ordering,
    and duplicate management.
    """
    
    def __init__(self, config: Optional[WorkLogConfig] = None):
        """Initialize with configuration."""
        self.config = config or WorkLogConfig()
    
    def add_entry_chronologically(self, daily_file: Path, new_entry: str) -> None:
        """
        Add entry to daily file maintaining chronological order and removing duplicates.
        
        Args:
            daily_file: Path to the daily log file
            new_entry: Formatted entry string to add
            
        Raises:
            IOError: If file operations fail
        """
        try:
            entries = []
            
            # Read existing entries if file exists
            if daily_file.exists():
                with open(daily_file, 'r', encoding='utf-8') as f:
                    entries = f.read().strip().split('\n')
                    entries = [entry for entry in entries if entry.strip()]
            
            # Extract task name from new entry for duplicate detection
            new_entry_parts = new_entry.split(' ', 2)
            if len(new_entry_parts) >= 3:
                new_task_identifier = new_entry_parts[2]
                
                # If this is a completion entry, remove existing entries for the same task
                if '(' in new_task_identifier and ')' in new_task_identifier:
                    task_name = new_task_identifier.split('(')[0].strip()
                    entries = [entry for entry in entries if not (
                        len(entry.split(' ', 2)) >= 3 and
                        entry.split(' ', 2)[2].startswith(task_name + ' ')
                    )]
            
            # Add new entry
            entries.append(new_entry)
            
            # Sort entries chronologically
            entries.sort(key=lambda x: x[:19] if len(x) >= 19 else x)
            
            # Write sorted entries back to file
            with open(daily_file, 'w', encoding='utf-8') as f:
                for entry in entries:
                    f.write(f"{entry}\n")
                    
            logger.debug(f"Added entry to daily file: {daily_file}")
            
        except Exception as e:
            logger.error(f"Failed to add entry to daily file {daily_file}: {e}")
            raise IOError(f"Daily file operation failed: {e}")
    
    def format_entry(self, task_name: str, action: str, timestamp: str, duration: Optional[str] = None) -> str:
        """
        Format a daily file entry based on action type.
        
        Args:
            task_name: Name of the task
            action: Type of action ('start', 'end', 'completed', 'pause', 'resume')
            timestamp: ISO timestamp
            duration: Optional duration string
            
        Returns:
            str: Formatted entry string
        """
        display_time = WorkLog._format_display_time(timestamp)
        display_name = "[ANONYMOUS WORK]" if task_name == WorkLog.ANONYMOUS_TASK_NAME else task_name
        
        if action == 'start':
            return f"{display_time} {display_name} [ACTIVE]"
        elif action == 'end' and duration:
            return f"{display_time} {display_name} ({duration})"
        elif action == 'completed' and duration:
            # For retroactive entries, calculate start time from duration
            start_dt = datetime.fromisoformat(timestamp)
            duration_parts = duration.split(':')
            hours, minutes, seconds = int(duration_parts[0]), int(duration_parts[1]), int(duration_parts[2])
            start_time = start_dt - timedelta(hours=hours, minutes=minutes, seconds=seconds)
            start_display = WorkLog._format_display_time(start_time.isoformat())
            return f"{start_display} {display_name} ({duration})"
        elif action == 'pause':
            return f"{display_time} {display_name} [PAUSED]"
        elif action == 'resume':
            return f"{display_time} {display_name} [RESUMED]"
        else:
            return f"{display_time} {display_name} [{action.upper()}]"

def requires_data(func):
    """
    Decorator that ensures worklog data is loaded before method execution.
    
    Args:
        func: Method to decorate
        
    Returns:
        Decorated function that loads data if needed
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, '_data') or self._data is None:
            self._data = self._load_data()
        return func(self, *args, **kwargs)
    return wrapper

def auto_save(func):
    """
    Decorator that automatically saves worklog data after method execution.
    
    Args:
        func: Method to decorate
        
    Returns:
        Decorated function that saves data after execution
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        self._save_data()
        return result
    return wrapper

class WorkLog:
    """
    Modern WorkLog class with comprehensive time tracking capabilities.
    
    This class provides a complete solution for tracking work time on tasks,
    including single-task and parallel modes, pause/resume functionality,
    anonymous work sessions, and organized daily logs.
    
    Enhanced with configuration management, validation, and structured logging.
    """
    
    ANONYMOUS_TASK_NAME = "__ANONYMOUS_WORK__"
    
    def __init__(self, config: Optional[WorkLogConfig] = None) -> None:
        """
        Initialize WorkLog with directory setup and data migration.
        
        Creates the worklog directory structure and migrates any existing
        data from the old format. Initializes the data structure for tracking
        tasks, active sessions, and paused work.
        
        Args:
            config: Optional configuration override
        """
        self.config = config or WorkLogConfig()
        self.validator = WorkLogValidator()
        self.daily_file_manager = DailyFileManager(self.config)
        
        self.worklog_dir = Path.home() / self.config.worklog_dir_name
        self.worklog_file = self.worklog_dir / 'worklog.json'
        self._data: Optional[WorkLogData] = None
        
        self._ensure_directory()
        self._migrate_old_file()
        
        logger.info(f"WorkLog initialized with directory: {self.worklog_dir}")
    
    @property
    def data(self) -> WorkLogData:
        """
        Lazy-loaded property for accessing worklog data.
        
        Returns:
            WorkLogData: Current worklog state with all tasks and sessions
        """
        if self._data is None:
            self._data = self._load_data()
        return self._data
    
    def _ensure_directory(self) -> None:
        """
        Create the worklog directory structure if it doesn't exist.
        
        Creates ~/.worklog directory with appropriate permissions for
        storing JSON database and daily text files.
        
        Raises:
            PermissionError: If unable to create directory due to permissions
            OSError: If directory creation fails for other reasons
        """
        try:
            self.worklog_dir.mkdir(exist_ok=True)
            logger.info(f"Directory ensured: {self.worklog_dir}")
        except PermissionError:
            console.print(
                f"❌ Permission denied creating worklog directory: {self.worklog_dir}\n"
                "💡 Try running with appropriate permissions or choose a different location.",
                style="red"
            )
            raise
        except OSError as e:
            console.print(
                f"❌ Failed to create worklog directory: {self.worklog_dir}\n"
                f"💥 Error: {e}",
                style="red"
            )
            raise
    
    def _migrate_old_file(self) -> None:
        """
        Migrate legacy worklog.json from home directory to new structure.
        
        Automatically detects and migrates existing ~/.worklog.json file
        to the new ~/.worklog/worklog.json location, preserving all
        historical data and maintaining backward compatibility.
        """
        old_file = Path.home() / '.worklog.json'
        if old_file.exists() and not self.worklog_file.exists():
            try:
                with open(old_file, 'r') as f:
                    data = f.read()
                with open(self.worklog_file, 'w') as f:
                    f.write(data)
                console.print(f"✅ Migrated worklog data to {self.worklog_file}")
                
                # Backup and remove old file
                backup_file = Path.home() / '.worklog.json.backup'
                old_file.rename(backup_file)
                console.print(f"📦 Backup created at {backup_file}")
                
            except Exception as e:
                console.print(f"❌ Migration failed: {e}", style="red")
    
    def _get_daily_file_path(self, date_str: Optional[str] = None) -> Path:
        """
        Generate path for daily worklog file.
        
        Args:
            date_str: Optional date string in YYYY-MM-DD format.
                     Defaults to current date if not provided.
        
        Returns:
            Path: Full path to the daily worklog text file
        
        Example:
            >>> worklog._get_daily_file_path("2025-10-03")
            Path('/home/user/.worklog/2025-10-03.txt')
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        return self.worklog_dir / f"{date_str}.txt"
    
    @contextmanager
    def _file_operation(self, file_path: Path, mode: str = 'r'):
        """
        Context manager for safe file operations with error handling.
        
        Args:
            file_path: Path to the file
            mode: File opening mode ('r', 'w', 'a', etc.)
            
        Yields:
            file object: Opened file handle
            
        Example:
            >>> with worklog._file_operation(path, 'w') as f:
            ...     f.write(content)
        """
        try:
            with open(file_path, mode, encoding='utf-8') as f:
                yield f
        except FileNotFoundError:
            if 'r' in mode:
                console.print(f"📄 File not found: {file_path}", style="yellow")
            raise
        except Exception as e:
            console.print(f"❌ File operation failed: {e}", style="red")
            raise
    
    def _update_daily_file(self, task_name: str, action: str, timestamp: str, duration: Optional[str] = None) -> None:
        """
        Update daily human-readable log file with task activity.
        
        Uses the DailyFileManager for consistent formatting and chronological ordering.
        
        Args:
            task_name: Name of the task being logged
            action: Type of action ('start', 'end', 'pause', 'resume', 'completed')
            timestamp: ISO timestamp of the action
            duration: Optional duration string for completed tasks
            
        Example:
            File content: "2025-10-03 14:30:00 Fix bug #123 (01:30:45)"
        """
        daily_file = self._get_daily_file_path()
        entry = self.daily_file_manager.format_entry(task_name, action, timestamp, duration)
        self.daily_file_manager.add_entry_chronologically(daily_file, entry)


    
    def _load_data(self) -> WorkLogData:
        """
        Load worklog data from JSON file with error handling and validation.
        
        Loads the complete worklog state from the JSON database, handling
        legacy formats and providing sensible defaults for missing fields.
        Performs data validation and structure migration as needed.
        
        Returns:
            WorkLogData: Complete worklog state with all tasks and sessions
            
        Raises:
            json.JSONDecodeError: If JSON file is corrupted
            FileNotFoundError: If worklog file doesn't exist (creates new)
        """
        if not self.worklog_file.exists():
            console.print("📝 Creating new worklog database", style="green")
            return WorkLogData()
        
        try:
            with self._file_operation(self.worklog_file) as f:
                raw_data = json.load(f)
            
            # Convert raw dict to structured data with validation
            entries = [
                TaskEntry(**entry) if isinstance(entry, dict) else TaskEntry(*entry)
                for entry in raw_data.get('entries', [])
            ]
            
            paused_tasks = [
                PausedTask(**task) if isinstance(task, dict) else PausedTask(*task)
                for task in raw_data.get('paused_tasks', [])
            ]
            
            return WorkLogData(
                entries=entries,
                active_tasks=raw_data.get('active_tasks', {}),
                paused_tasks=paused_tasks,
                recent_tasks=raw_data.get('recent_tasks', [])
            )
            
        except json.JSONDecodeError as e:
            console.print(f"❌ Corrupted worklog file: {e}", style="red")
            console.print("🔄 Creating backup and starting fresh", style="yellow")
            
            # Create backup of corrupted file
            backup_file = self.worklog_file.with_suffix('.json.corrupted')
            try:
                self.worklog_file.rename(backup_file)
                console.print(f"💾 Corrupted file saved as: {backup_file}", style="dim")
            except OSError as backup_error:
                console.print(f"⚠️  Could not backup corrupted file: {backup_error}", style="yellow")
            
            logger.warning(f"JSON corruption in {self.worklog_file}: {e}")
            return WorkLogData()
        except Exception as e:
            console.print(
                f"❌ Unexpected error loading worklog data: {e}\n"
                "💡 Please check file permissions and disk space.",
                style="red"
            )
            logger.error(f"Unexpected error loading data: {e}")
            raise
    
    def _save_data(self) -> None:
        """
        Save worklog data to JSON file with atomic writes and error handling.
        
        Performs atomic write operation to prevent data corruption during
        save operations. Converts dataclass objects to JSON-serializable
        format while preserving all structure and metadata.
        
        Automatically sorts entries chronologically by start_time to maintain
        proper time sequence in both JSON database and daily files.
        
        Raises:
            IOError: If unable to write to disk
            json.JSONEncodeError: If data cannot be serialized
        """
        # Sort entries chronologically by start_time before saving (ISO strings sort correctly)
        self.data.entries.sort(key=lambda entry: entry.start_time if isinstance(entry.start_time, str) else entry.start_time.isoformat())
        
        # Convert dataclasses to dictionaries for JSON serialization
        data_dict = {
            'entries': [entry.__dict__ for entry in self.data.entries],
            'active_tasks': self.data.active_tasks,
            'paused_tasks': [task.__dict__ for task in self.data.paused_tasks],
            'recent_tasks': self.data.recent_tasks
        }
        
        # Atomic write: write to temp file then rename
        temp_file = self.worklog_file.with_suffix('.tmp')
        try:
            with self._file_operation(temp_file, 'w') as f:
                json.dump(data_dict, f, indent=2, ensure_ascii=False)
            temp_file.replace(self.worklog_file)
            logger.debug(f"Data saved successfully to {self.worklog_file}")
        except json.JSONEncodeError as e:
            console.print(f"❌ Failed to serialize worklog data: {e}", style="red")
            logger.error(f"JSON encoding error: {e}")
            if temp_file.exists():
                temp_file.unlink()
            raise
        except (IOError, OSError) as e:
            console.print(
                f"❌ Failed to save worklog data: {e}\n"
                "💡 Check available disk space and file permissions.",
                style="red"
            )
            logger.error(f"IO error saving data: {e}")
            if temp_file.exists():
                temp_file.unlink()
            raise
        except Exception as e:
            console.print(f"❌ Unexpected error saving data: {e}", style="red")
            logger.error(f"Unexpected error saving data: {e}")
            if temp_file.exists():
                temp_file.unlink()
            raise
    
    @staticmethod
    def _get_current_timestamp() -> str:
        """
        Generate current timestamp in ISO format.
        
        Returns:
            str: Current timestamp in ISO 8601 format
            
        Example:
            >>> WorkLog._get_current_timestamp()
            '2025-10-03T14:30:15.123456'
        """
        return datetime.now().isoformat()
    
    @staticmethod
    def _parse_custom_time(time_str: str) -> str:
        """
        Parse and validate HH:MM time string for custom start times.
        
        Converts HH:MM format to a full datetime for today, with comprehensive
        validation using centralized validation logic.
        
        Args:
            time_str: Time string in HH:MM format (e.g., "09:30", "14:45")
            
        Returns:
            str: ISO timestamp for today at the specified time
            
        Raises:
            ValueError: If time format is invalid or values out of range
            
        Example:
            >>> WorkLog._parse_custom_time("09:30")
            '2025-10-03T09:30:00'
        """
        # Use centralized validation
        hours, minutes = WorkLogValidator.validate_time_format(time_str)
        
        # Create datetime for today at specified time
        today = datetime.now().date()
        custom_datetime = datetime.combine(
            today, 
            datetime.min.time().replace(hour=hours, minute=minutes)
        )
        
        return custom_datetime.isoformat()
    
    def _get_timestamp(self, custom_time: Optional[str] = None) -> str:
        """
        Get timestamp - current time or custom time for today.
        
        Args:
            custom_time: Optional HH:MM time string for backdating
            
        Returns:
            str: ISO timestamp (current or custom for today)
            
        Example:
            >>> worklog._get_timestamp("09:30")  # Custom time
            '2025-10-03T09:30:00'
            >>> worklog._get_timestamp()  # Current time
            '2025-10-03T14:30:15.123456'
        """
        if custom_time:
            return self._parse_custom_time(custom_time)
        return self._get_current_timestamp()
    
    @staticmethod
    def _format_duration(start_time: str, end_time: str) -> str:
        """
        Calculate and format duration between two timestamps.
        
        Computes the time difference between start and end timestamps,
        returning a human-readable duration in HH:MM:SS format.
        Handles timezone-aware and naive timestamps consistently.
        
        Args:
            start_time: ISO timestamp when task started
            end_time: ISO timestamp when task ended
            
        Returns:
            str: Formatted duration string (HH:MM:SS)
            
        Example:
            >>> WorkLog._format_duration("2025-10-03T09:00:00", "2025-10-03T10:30:15")
            '01:30:15'
        """
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time)
        duration = end_dt - start_dt
        
        # Convert to total seconds and format as HH:MM:SS
        total_seconds = int(duration.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    @staticmethod
    @lru_cache(maxsize=128)
    def _format_display_time(timestamp: str) -> str:
        """
        Format timestamp for human-readable display with caching.
        
        Args:
            timestamp: ISO timestamp string
            
        Returns:
            str: Formatted datetime string (YYYY-MM-DD HH:MM:SS)
            
        Example:
            >>> WorkLog._format_display_time("2025-10-03T14:30:15.123456")
            '2025-10-03 14:30:15'
        """
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def _format_start_time_compact(timestamp: str) -> str:
        """
        Format timestamp for compact display (time only).
        
        Args:
            timestamp: ISO timestamp string
            
        Returns:
            str: Formatted time string (HH:MM:SS)
            
        Example:
            >>> WorkLog._format_start_time_compact("2025-10-03T14:30:15.123456")
            '14:30:15'
        """
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%H:%M:%S")

    @requires_data
    @auto_save
    def start_task(self, task_name: str, custom_start_time: Optional[str] = None) -> bool:
        """
        Start tracking a new task with optional custom start time.
        
        Initiates time tracking for a named task, handling duplicate detection
        and integration with single-task vs parallel modes. Supports backdating
        entries with custom start times for accurate time tracking.
        
        Args:
            task_name: Unique identifier for the task to start
            custom_start_time: Optional HH:MM time for backdating entry
            
        Returns:
            bool: True if task started successfully, False if already active
            
        Example:
            >>> worklog.start_task("Bug fix #123")
            True
            >>> worklog.start_task("Morning meeting", "09:00")
            True
        """
        start_time = self._get_timestamp(custom_start_time)
        display_name = "[ANONYMOUS WORK]" if task_name == self.ANONYMOUS_TASK_NAME else task_name
        
        # Check for duplicate active task
        if task_name in self.data.active_tasks:
            existing_time = self.data.active_tasks[task_name]
            console.print(
                f"⚠️  Task '{display_name}' already active since {self._format_display_time(existing_time)}",
                style="yellow"
            )
            return False
        
        # Register active task and create entry
        self.data.active_tasks[task_name] = start_time
        entry = TaskEntry(
            task=task_name,
            start_time=start_time,
            end_time=None,
            duration=None
        )
        self.data.entries.append(entry)
        
        # Update daily log file
        self._update_daily_file(task_name, 'start', start_time)
        
        console.print(
            f"✅ Started tracking: '{display_name}' at {self._format_display_time(start_time)}",
            style="green"
        )
        return True

    @requires_data
    def start_anonymous_task(self) -> bool:
        """
        Start anonymous work session or resume last paused task.
        
        Provides flexible workflow for starting work when the specific task
        is not yet determined. Automatically resumes paused tasks if available,
        otherwise starts a new anonymous session to be named later.
        
        Returns:
            bool: True if session started/resumed successfully
            
        Example:
            >>> worklog.start_anonymous_task()
            True  # Starts anonymous session or resumes paused task
        """
        # Priority 1: Resume paused tasks if available
        if self.data.paused_tasks:
            return self.resume_last_task()
        
        # Priority 2: Check for existing anonymous session
        if self.ANONYMOUS_TASK_NAME in self.data.active_tasks:
            existing_time = self.data.active_tasks[self.ANONYMOUS_TASK_NAME]
            console.print(
                f"📝 Anonymous session already active since {self._format_display_time(existing_time)}",
                style="yellow"
            )
            return False
        
        # Start new anonymous session
        result = self.start_task(self.ANONYMOUS_TASK_NAME)
        if result:
            console.print("💡 Use 'worklog \"Task Name\"' to assign a name to this session", style="blue")
        return result

    def start_anonymous_task_at_time(self, custom_time: str) -> bool:
        """
        Start anonymous work session at specific time.
        
        Combines anonymous task functionality with custom start time support
        for backdating entries when the work session details are determined
        after the fact.
        
        Args:
            custom_time: HH:MM time string for the session start
            
        Returns:
            bool: True if session started successfully
            
        Raises:
            ValueError: If time format is invalid
            
        Example:
            >>> worklog.start_anonymous_task_at_time("08:30")
            True
        """
        # Check for existing anonymous session
        if self.ANONYMOUS_TASK_NAME in self.data.active_tasks:
            existing_time = self.data.active_tasks[self.ANONYMOUS_TASK_NAME]
            console.print(
                f"📝 Anonymous session already active since {self._format_display_time(existing_time)}",
                style="yellow"
            )
            return False
        
        # Start anonymous session with custom time
        result = self.start_task(self.ANONYMOUS_TASK_NAME, custom_time)
        if result:
            console.print("💡 Use 'worklog \"Task Name\"' to assign a name to this session", style="blue")
        return result

    @requires_data
    @auto_save
    def end_task(self, task_name: str) -> bool:
        """
        End tracking for an active task and calculate final duration.
        
        Completes time tracking for an active task, calculating total duration
        and updating both JSON database and daily log files. Handles task
        cleanup and provides comprehensive completion summary.
        
        Args:
            task_name: Name of the task to end
            
        Returns:
            bool: True if task ended successfully, False if not active
            
        Example:
            >>> worklog.end_task("Bug fix #123")
            True  # Task completed with duration calculated
        """
        # Validate task is active
        if task_name not in self.data.active_tasks:
            display_name = "[ANONYMOUS WORK]" if task_name == self.ANONYMOUS_TASK_NAME else task_name
            console.print(f"❌ Task '{display_name}' is not currently active", style="red")
            return False
        
        # Calculate completion details
        start_time = self.data.active_tasks[task_name]
        end_time = self._get_current_timestamp()
        duration = self._format_duration(start_time, end_time)
        
        # Update the most recent entry for this task
        for entry in reversed(self.data.entries):
            if entry.task == task_name and entry.end_time is None:
                entry.end_time = end_time
                entry.duration = duration
                break
        
        # Clean up active task tracking
        del self.data.active_tasks[task_name]
        
        # Update recent tasks list (for resume functionality)
        if task_name in self.data.recent_tasks:
            self.data.recent_tasks.remove(task_name)
        self.data.recent_tasks.append(task_name)
        
        # Keep recent tasks list manageable
        if len(self.data.recent_tasks) > 10:
            self.data.recent_tasks = self.data.recent_tasks[-10:]
        
        # Update daily log file
        self._update_daily_file(task_name, 'end', end_time, duration)
        
        # Display completion summary
        display_name = "[ANONYMOUS WORK]" if task_name == self.ANONYMOUS_TASK_NAME else task_name
        console.print(f"✅ Completed: '{display_name}' at {self._format_display_time(end_time)}", style="green")
        console.print(f"⏱️  Duration: {duration}", style="blue")
        
        return True

    @requires_data
    def handle_task(self, task_name: str, parallel_mode: bool = False, custom_start_time: Optional[str] = None) -> bool:
        """
        Smart task handler - starts or ends tasks based on current state.
        
        Provides intelligent task management by detecting current state and
        taking appropriate action. Handles anonymous task conversion, parallel
        vs single-task modes, and integrates custom start time functionality.
        
        Args:
            task_name: Name of the task to start or end
            parallel_mode: Allow concurrent tasks (default: single-task mode)
            custom_start_time: Optional HH:MM time for backdating new tasks
            
        Returns:
            bool: True if operation completed successfully
            
        Example:
            >>> worklog.handle_task("Debug session")  # Start task
            True
            >>> worklog.handle_task("Debug session")  # End same task  
            True
        """
        # Handle anonymous task conversion to named task
        if (self.ANONYMOUS_TASK_NAME in self.data.active_tasks and 
            task_name != self.ANONYMOUS_TASK_NAME and 
            task_name not in self.data.active_tasks):
            return self._convert_anonymous_task(task_name)
        
        # End task if currently active
        if task_name in self.data.active_tasks:
            if custom_start_time:
                console.print("⚠️  --start-time ignored when ending a task", style="yellow")
            return self.end_task(task_name)
        
        # Start new task with mode-appropriate setup
        else:
            # Single-task mode: stop other active tasks
            if not parallel_mode and self.data.active_tasks:
                stopped_count = self._stop_other_tasks(exclude_task=task_name)
                if stopped_count > 0:
                    console.print("🔄 Single-task mode: stopped previous tasks", style="yellow")
            
            return self.start_task(task_name, custom_start_time)

    @requires_data
    @auto_save  
    def _convert_anonymous_task(self, new_task_name: str) -> bool:
        """
        Convert active anonymous session to a named task.
        
        Seamlessly transitions an anonymous work session to a named task
        without losing time tracking data. Updates all references and
        maintains accurate time accounting throughout the conversion.
        
        Args:
            new_task_name: Name to assign to the anonymous session
            
        Returns:
            bool: True if conversion completed successfully
            
        Example:
            >>> # Anonymous session running
            >>> worklog._convert_anonymous_task("Important project")
            True  # Session now named "Important project"
        """
        if self.ANONYMOUS_TASK_NAME not in self.data.active_tasks:
            return False
        
        # Transfer active session to new name
        start_time = self.data.active_tasks[self.ANONYMOUS_TASK_NAME]
        del self.data.active_tasks[self.ANONYMOUS_TASK_NAME]
        self.data.active_tasks[new_task_name] = start_time
        
        # Update the most recent entry
        for entry in reversed(self.data.entries):
            if entry.task == self.ANONYMOUS_TASK_NAME and entry.end_time is None:
                entry.task = new_task_name
                break
        
        # Update daily file by replacing the last anonymous entry
        self._update_anonymous_daily_file(new_task_name, start_time)
        
        console.print(f"✅ Converted anonymous session to: '{new_task_name}'", style="green")
        return True

    def _update_anonymous_daily_file(self, new_task_name: str, start_time: str) -> None:
        """
        Update daily file to replace anonymous task entry with named task.
        
        Maintains clean daily logs by replacing the most recent anonymous
        work entry with the actual task name, preserving timing accuracy
        while improving log readability.
        
        Args:
            new_task_name: New name for the task
            start_time: Original start time of the anonymous session
        """
        daily_file = self._get_daily_file_path()
        if not daily_file.exists():
            # Create new entry if daily file doesn't exist
            self._update_daily_file(new_task_name, 'start', start_time)
            return
        
        try:
            # Read current daily file content
            with self._file_operation(daily_file, 'r') as f:
                lines = f.readlines()
            
            # Find and replace the last anonymous entry
            display_time = self._format_display_time(start_time)
            old_entry = f"{display_time} [ANONYMOUS WORK] [ACTIVE]"
            new_entry = f"{display_time} {new_task_name} [ACTIVE]"
            
            # Replace from the end to get the most recent entry
            for i in range(len(lines) - 1, -1, -1):
                if old_entry in lines[i]:
                    lines[i] = f"{new_entry}\n"
                    break
            
            # Write updated content back to file
            with self._file_operation(daily_file, 'w') as f:
                f.writelines(lines)
                
        except Exception as e:
            console.print(f"⚠️  Could not update daily file: {e}", style="yellow")
            # Fallback: add new entry
            self._update_daily_file(new_task_name, 'start', start_time)

    @requires_data  
    @auto_save
    def _stop_other_tasks(self, exclude_task: Optional[str] = None) -> int:
        """
        Stop all active tasks except the specified exclusion.
        
        Implements single-task mode by ending all currently active tasks
        before starting a new one. Provides clean task switching with
        duration calculations and proper logging.
        
        Args:
            exclude_task: Task name to keep running (not stop)
            
        Returns:
            int: Number of tasks that were stopped
            
        Example:
            >>> worklog._stop_other_tasks(exclude_task="Keep running")
            2  # Stopped 2 other active tasks
        """
        tasks_to_stop = [
            task for task in self.data.active_tasks.keys()
            if task != exclude_task
        ]
        
        stopped_tasks = []
        for task_name in tasks_to_stop:
            start_time = self.data.active_tasks[task_name]
            end_time = self._get_current_timestamp()
            duration = self._format_duration(start_time, end_time)
            
            # Update entry with completion details
            for entry in reversed(self.data.entries):
                if entry.task == task_name and entry.end_time is None:
                    entry.end_time = end_time  
                    entry.duration = duration
                    break
            
            # Update daily file and tracking
            self._update_daily_file(task_name, 'end', end_time, duration)
            del self.data.active_tasks[task_name]
            
            display_name = "[ANONYMOUS WORK]" if task_name == self.ANONYMOUS_TASK_NAME else task_name
            stopped_tasks.append(f"  - {display_name} ({duration})")
        
        # Display summary of stopped tasks
        if stopped_tasks:
            console.print("Stopped previous task(s) (single-task mode):")
            for task_info in stopped_tasks:
                console.print(task_info, style="yellow")
        
        return len(stopped_tasks)

    @requires_data
    @auto_save
    def stop_all_tasks(self) -> None:
        """
        Stop all active and clear all paused tasks.
        
        Provides end-of-day cleanup functionality by stopping all active
        task tracking and clearing paused task queue. Calculates final
        durations and provides comprehensive completion summary.
        
        Example:
            >>> worklog.stop_all_tasks()
            # Stops all active tasks, clears all paused tasks
        """
        active_stopped = []
        paused_cleared = []
        
        # Stop all active tasks with duration calculation
        for task_name in [*self.data.active_tasks.keys()]:
            start_time = self.data.active_tasks[task_name]
            end_time = self._get_current_timestamp()
            duration = self._format_duration(start_time, end_time)
            
            # Complete the entry
            for entry in reversed(self.data.entries):
                if entry.task == task_name and entry.end_time is None:
                    entry.end_time = end_time
                    entry.duration = duration
                    break
            
            # Update daily file and clean up
            self._update_daily_file(task_name, 'end', end_time, duration)
            del self.data.active_tasks[task_name]
            
            display_name = "[ANONYMOUS WORK]" if task_name == self.ANONYMOUS_TASK_NAME else task_name
            active_stopped.append(f"  - {display_name} ({duration})")
        
        # Clear all paused tasks
        for paused_task in self.data.paused_tasks:
            display_name = "[ANONYMOUS WORK]" if paused_task.task == self.ANONYMOUS_TASK_NAME else paused_task.task
            paused_cleared.append(f"  - {display_name} (total: {paused_task.total_duration_so_far})")
        
        self.data.paused_tasks.clear()
        
        # Display comprehensive summary
        if active_stopped:
            console.print("✅ Stopped active task(s):", style="green")
            for task in active_stopped:
                console.print(task)
        
        if paused_cleared:
            console.print("🗑️  Cleared paused task(s):", style="blue")  
            for task in paused_cleared:
                console.print(task)
        
        if not active_stopped and not paused_cleared:
            console.print("ℹ️  No active or paused tasks to stop", style="blue")

    @requires_data
    @auto_save
    def pause_all_tasks(self) -> None:
        """
        Pause all active tasks for later resumption.
        
        Temporarily suspends all active task tracking while preserving
        accumulated time. Enables break functionality where work can be
        resumed later without losing time accounting accuracy.
        
        Example:
            >>> worklog.pause_all_tasks()  
            # All active tasks moved to paused state
        """
        if not self.data.active_tasks:
            console.print("ℹ️  No active tasks to pause", style="blue")
            return
        
        paused_count = 0
        for task_name in [*self.data.active_tasks.keys()]:
            start_time = self.data.active_tasks[task_name]
            pause_time = self._get_current_timestamp()
            
            # Calculate duration for this session
            session_duration = self._format_duration(start_time, pause_time)
            
            # Calculate total accumulated time for this task
            total_duration = self._calculate_total_duration(task_name)
            
            # Create paused task record
            paused_task = PausedTask(
                task=task_name,
                total_duration_so_far=total_duration,
                last_paused_at=pause_time
            )
            self.data.paused_tasks.append(paused_task)
            
            # Update entry and cleanup active tracking
            for entry in reversed(self.data.entries):
                if entry.task == task_name and entry.end_time is None:
                    entry.end_time = pause_time
                    entry.duration = session_duration
                    break
            
            del self.data.active_tasks[task_name]
            self._update_daily_file(task_name, 'pause', pause_time, session_duration)
            
            display_name = "[ANONYMOUS WORK]" if task_name == self.ANONYMOUS_TASK_NAME else task_name
            console.print(f"⏸️  Paused: '{display_name}' (session: {session_duration})")
            paused_count += 1
        
        console.print(f"✅ Paused {paused_count} task(s)", style="green")

    @requires_data
    def _calculate_total_duration(self, task_name: str) -> str:
        """
        Calculate total accumulated time for a task across all sessions.
        
        Sums up duration from all completed entries for a specific task,
        providing comprehensive time tracking across multiple work sessions.
        Used for pause/resume functionality and reporting.
        
        Args:
            task_name: Name of the task to calculate time for
            
        Returns:
            str: Total duration in HH:MM:SS format
            
        Example:
            >>> worklog._calculate_total_duration("Bug fix #123")
            '03:45:30'  # Total across all sessions
        """
        total_seconds = 0
        
        # Sum durations from all completed entries
        for entry in self.data.entries:
            if entry.task == task_name and entry.duration:
                # Parse duration string (HH:MM:SS) to seconds
                time_parts = entry.duration.split(':')
                hours, minutes, seconds = map(int, time_parts)
                entry_seconds = hours * 3600 + minutes * 60 + seconds
                total_seconds += entry_seconds
        
        # Convert back to HH:MM:SS format
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @requires_data
    @auto_save
    def resume_last_task(self) -> bool:
        """
        Resume the most recently paused task.
        
        Restarts time tracking for the last paused task, maintaining
        continuity in time accounting while providing seamless workflow
        resumption. Displays accumulated time for context.
        
        Returns:
            bool: True if task resumed successfully, False if none available
            
        Example:
            >>> worklog.resume_last_task()
            True  # Resumed "Bug fix #123" with previous time: 01:30:45
        """
        if not self.data.paused_tasks:
            console.print("ℹ️  No paused tasks to resume", style="blue")
            return False
        
        # Get most recent paused task
        last_paused = self.data.paused_tasks[-1]
        task_name = last_paused.task
        
        # Check for conflicts with active tasks
        if task_name in self.data.active_tasks:
            display_name = "[ANONYMOUS WORK]" if task_name == self.ANONYMOUS_TASK_NAME else task_name
            console.print(f"⚠️  Task '{display_name}' is already active", style="yellow")
            return False
        
        # Resume the task
        current_time = self._get_current_timestamp()
        self.data.active_tasks[task_name] = current_time
        
        # Create new entry for resumed session
        entry = TaskEntry(
            task=task_name,
            start_time=current_time,
            end_time=None,
            duration=None
        )
        self.data.entries.append(entry)
        
        # Remove from paused tasks
        self.data.paused_tasks.remove(last_paused)
        
        # Update daily file
        self._update_daily_file(task_name, 'resume', current_time)
        
        # Display resumption summary
        display_name = "[ANONYMOUS WORK]" if task_name == self.ANONYMOUS_TASK_NAME else task_name
        console.print(f"▶️  Resumed: '{display_name}' at {self._format_display_time(current_time)}", style="green")
        console.print(f"⏱️  Previous total: {last_paused.total_duration_so_far}", style="blue")
        
        return True

    @requires_data
    def clean_today_worklog(self) -> None:
        """
        Clean today's worklog entries with confirmation and backup.
        
        Provides safe cleanup functionality for removing today's work log
        entries. Creates comprehensive backup, requires explicit user
        confirmation, and handles both JSON database and daily file cleanup.
        
        Example:
            >>> worklog.clean_today_worklog()
            # Interactive cleanup with backup creation
        """
        today_str = datetime.now().strftime("%Y-%m-%d")
        self.clean_date_worklog(today_str)

    @requires_data
    @auto_save
    def clean_date_worklog(self, date_str: str) -> None:
        """
        Clean worklog entries for a specific date with confirmation and backup.
        
        Provides safe cleanup functionality for removing work log entries
        from any specified date. Creates comprehensive backup, requires 
        explicit user confirmation, and handles both JSON database and 
        daily file cleanup.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Example:
            >>> worklog.clean_date_worklog("2025-10-01")
            # Interactive cleanup with backup creation for Oct 1st
        """
        daily_file = self._get_daily_file_path(date_str)
        
        # Identify entries to clean
        date_entries = [
            entry for entry in self.data.entries 
            if entry.start_time.startswith(date_str)
        ]
        
        if not date_entries and not daily_file.exists():
            console.print(f"ℹ️  No worklog entries found for {date_str}", style="blue")
            return
        
        # Show cleanup preview
        console.print(f"🔍 Found {len(date_entries)} entries for {date_str}")
        if daily_file.exists():
            console.print(f"📄 Daily file: {daily_file}")
        
        # Request confirmation
        confirm = typer.confirm(f"Are you sure you want to clean worklog for {date_str}?")
        if not confirm:
            console.print("❌ Clean operation cancelled", style="yellow")
            return
        
        # Create comprehensive backup
        if date_entries or daily_file.exists():
            backup_data = {
                'json_entries': date_entries,
                'daily_file': daily_file if daily_file.exists() else None,
                'active_tasks': {
                    task: start_time for task, start_time in self.data.active_tasks.items()
                    if start_time.startswith(date_str)
                }
            }
            backup_file = self.backup_manager.create_backup(
                backup_type='clean',
                data=backup_data,
                suffix=f"clean_{date_str}"
            )
            console.print(f"💾 Backup created: {backup_file}", style="green")
        
        # Clean JSON entries
        if date_entries:
            self.data.entries = [
                entry for entry in self.data.entries 
                if not entry.start_time.startswith(date_str)
            ]
            
            # Clean active tasks for this date
            active_to_remove = [
                task for task, start_time in self.data.active_tasks.items()
                if start_time.startswith(date_str)
            ]
            
            for task in active_to_remove:
                del self.data.active_tasks[task]
            
            console.print(f"✅ Cleaned {len(date_entries)} JSON entries", style="green")
        
        # Clean daily file
        if daily_file.exists():
            daily_file.unlink()
            console.print(f"🗑️  Removed daily file: {daily_file}", style="green")
        
        console.print(f"✨ Clean completed for {date_str}", style="green bold")

    @requires_data
    def list_active_tasks(self) -> None:
        """
        Display all currently active tasks or today's log if none active.
        
        Provides comprehensive status overview showing either active task
        tracking or today's completed work history. Uses rich formatting
        for enhanced readability and visual appeal.
        
        Example:
            >>> worklog.list_active_tasks()
            # Shows active tasks table or today's work summary
        """
        if not self.data.active_tasks:
            console.print("ℹ️  NO ACTIVE TASKS", style="blue bold")
            console.print()
            self.show_today_file()
            return
        
        # Create rich table for active tasks
        table = Table(title="🔥 Active Tasks", show_header=True, header_style="bold magenta")
        table.add_column("Task", style="cyan", no_wrap=False)
        table.add_column("Started At", style="green")
        table.add_column("Duration", style="yellow")
        
        current_time = self._get_current_timestamp()
        for task_name, start_time in self.data.active_tasks.items():
            display_name = "[ANONYMOUS WORK]" if task_name == self.ANONYMOUS_TASK_NAME else task_name
            formatted_start = self._format_display_time(start_time)
            duration = self._format_duration(start_time, current_time)
            
            table.add_row(display_name, formatted_start, duration)
        
        console.print(table)

    @requires_data
    def show_recent_entries(self, count: int = 10) -> None:
        """
        Display recent worklog entries with rich formatting.
        
        Shows the most recent completed task entries in a clean, scannable
        format. Provides quick overview of recent work activity with
        timestamps and durations for productivity tracking.
        
        Args:
            count: Number of recent entries to display (default: 10)
            
        Example:
            >>> worklog.show_recent_entries(5)
            # Shows last 5 completed tasks
        """
        completed_entries = [
            entry for entry in self.data.entries 
            if entry.end_time is not None
        ]
        
        if not completed_entries:
            console.print("ℹ️  No completed entries found", style="blue")
            return
        
        # Get most recent entries
        recent_entries = completed_entries[-count:]
        
        console.print(f"📊 Recent {len(recent_entries)} entries:", style="bold")
        console.print()
        
        for entry in reversed(recent_entries):
            display_name = "[ANONYMOUS WORK]" if entry.task == self.ANONYMOUS_TASK_NAME else entry.task
            start_compact = self._format_start_time_compact(entry.start_time)
            date_part = entry.start_time[:10]  # YYYY-MM-DD
            
            console.print(f"  {date_part} {start_compact} {display_name} ({entry.duration})")

    def show_today_file(self) -> None:
        """
        Display today's daily worklog file with rich formatting.
        
        Shows the human-readable daily log for today, providing a clean
        overview of all task activity. Handles missing files gracefully
        and uses consistent formatting for easy scanning.
        
        Example:
            >>> worklog.show_today_file()
            # Displays today's work activity from daily file
        """
        daily_file = self._get_daily_file_path()
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        if not daily_file.exists():
            console.print(f"ℹ️  No worklog file found for {today_str}", style="blue")
            return
        
        try:
            console.print(f"📅 Today's worklog ({today_str}):", style="bold")
            console.print()
            
            with self._file_operation(daily_file, 'r') as f:
                content = f.read().strip()
                if content:
                    console.print(content)
                else:
                    console.print("  (empty)", style="dim")
                    
        except Exception as e:
            console.print(f"❌ Error reading today's file: {e}", style="red")

    def show_date_file(self, date_str: str) -> None:
        """
        Display worklog file for a specific date with validation.
        
        Shows historical work activity for any specified date with
        comprehensive error handling and date format validation.
        Provides consistent formatting across all date views.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Example:
            >>> worklog.show_date_file("2025-10-02") 
            # Shows work activity for October 2nd, 2025
        """
        try:
            # Validate date format
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            console.print(f"❌ Invalid date format: {date_str}. Use YYYY-MM-DD", style="red")
            return
        
        daily_file = self._get_daily_file_path(date_str)
        
        if not daily_file.exists():
            console.print(f"ℹ️  No worklog file found for {date_str}", style="blue")
            return
        
        try:
            console.print(f"📅 Worklog for {date_str}:", style="bold")
            console.print()
            
            with self._file_operation(daily_file, 'r') as f:
                content = f.read().strip()
                if content:
                    console.print(content)
                else:
                    console.print("  (empty)", style="dim")
                    
        except Exception as e:
            console.print(f"❌ Error reading file for {date_str}: {e}", style="red")

    @requires_data
    @auto_save
    def add_retroactive_entry(self, task_name: str, start_time_str: str, stop_time_str: str) -> None:
        """
        Add a completed work session with custom start and stop times.
        
        Enables retroactive logging of work sessions that occurred in the past.
        Validates time format, ensures logical time sequence, and adds the
        completed entry to both JSON database and appropriate daily file.
        
        Args:
            task_name: Name of the task that was completed
            start_time_str: Start time in HH:MM format
            stop_time_str: Stop time in HH:MM format
            
        Raises:
            ValueError: If time format is invalid or stop_time <= start_time
            
        Example:
            >>> worklog.add_retroactive_entry("Meeting", "09:00", "10:30")
            ✅ Added retroactive entry: 'Meeting' (01:30:00)
        """
        try:
            # Parse and validate times
            start_timestamp = self._parse_custom_time(start_time_str)
            stop_timestamp = self._parse_custom_time(stop_time_str)
            
            # Ensure stop time is after start time
            start_dt = datetime.fromisoformat(start_timestamp)
            stop_dt = datetime.fromisoformat(stop_timestamp)
            
            if stop_dt <= start_dt:
                raise ValueError("Stop time must be after start time")
                
            # Calculate duration
            duration = self._format_duration(start_timestamp, stop_timestamp)
            
            # Create completed entry (store as ISO strings for JSON compatibility)
            entry = TaskEntry(
                task=task_name,
                start_time=start_timestamp,
                end_time=stop_timestamp,
                duration=duration
            )
            
            # Add to entries list
            self.data.entries.append(entry)
            
            # Write to daily file
            self._update_daily_file(task_name, "completed", stop_timestamp, duration)
            
            # Success feedback
            display_name = "[ANONYMOUS WORK]" if task_name == self.ANONYMOUS_TASK_NAME else task_name
            start_display = self._format_display_time(start_timestamp)
            stop_display = self._format_display_time(stop_timestamp)
            
            console.print(f"✅ Added retroactive entry: '{display_name}' ({duration})", style="green")
            console.print(f"📅 {start_display} → {stop_display}", style="dim")
            
        except ValueError as e:
            raise ValueError(f"Invalid time format or sequence: {e}")

# Typer CLI Commands

@app.command()
def task(
    task_name: str = typer.Argument(help="Task name to start or end"),
    parallel: bool = typer.Option(False, "--parallel", "-pl", "-p", help="Allow multiple concurrent tasks"),
    start_time: Optional[str] = typer.Option(None, "--start-time", "-t", help="Custom start time (HH:MM)"),
    stop_time: Optional[str] = typer.Option(None, "--stop-time", help="Custom stop time (HH:MM) for retroactive entries")
) -> None:
    """
    🎯 Start or end a specific task.
    
    Toggle behavior: first run starts the task, second run ends it.
    Single-task mode by default (stops other tasks unless --parallel used).
    
    Retroactive logging: Use both --start-time and --stop-time to add completed work sessions.
    """
    worklog = WorkLog()
    
    # Handle retroactive logging when both start_time and stop_time are provided
    if start_time and stop_time:
        try:
            worklog.add_retroactive_entry(task_name, start_time, stop_time)
        except ValueError as e:
            console.print(f"❌ {e}", style="red")
            raise typer.Exit(1)
    elif start_time:
        try:
            worklog.handle_task(task_name, parallel, start_time)
        except ValueError as e:
            console.print(f"❌ {e}", style="red")
            raise typer.Exit(1)
    elif stop_time:
        console.print("❌ --stop-time requires --start-time for retroactive entries", style="red")
        raise typer.Exit(1)
    else:
        worklog.handle_task(task_name, parallel)

@app.command("start", short_help="🚀 Start anonymous work")
def start(
    start_time: Optional[str] = typer.Option(None, "--start-time", "-t", help="Custom start time (HH:MM)")
) -> None:
    """
    🚀 Start anonymous work session OR resume last paused task.
    
    Smart behavior: resumes paused tasks if available, otherwise starts anonymous session.
    Use 'worklog task "Task Name"' later to assign a name to anonymous sessions.
    """
    worklog = WorkLog()
    
    if start_time:
        try:
            worklog.start_anonymous_task_at_time(start_time)
        except ValueError as e:
            console.print(f"❌ {e}", style="red")
            raise typer.Exit(1)
    else:
        worklog.start_anonymous_task()

@app.command("stop", short_help="⏹️ Stop all active tasks")
def stop() -> None:
    """
    ⏹️ Stop ALL active and paused tasks.
    
    End-of-day cleanup: stops all active tasks and clears paused task queue.
    """
    worklog = WorkLog()
    worklog.stop_all_tasks()

@app.command("pause", short_help="⏸️ Pause all active tasks")
def pause() -> None:
    """
    ⏸️ Pause all active tasks (can be resumed later).
    
    Temporarily suspend all active tasks while preserving time tracking.
    Use 'resume' or 'start' to continue work.
    """
    worklog = WorkLog()
    worklog.pause_all_tasks()

@app.command("resume", short_help="▶️ Resume last paused task")
def resume() -> None:
    """
    ▶️ Resume the last paused task.
    
    Restart time tracking for the most recently paused task.
    """
    worklog = WorkLog()
    worklog.resume_last_task()

@app.command("clean", short_help="🧹 Clean worklog entries")
def clean(
    date: Optional[str] = typer.Option(None, "--date", "-d", help="Specific date to clean (YYYY-MM-DD). Default: today")
) -> None:
    """
    🧹 Clean worklog entries (with confirmation and backup).
    
    Remove entries from both JSON database and daily file for the specified date.
    Creates backup before deletion and requires user confirmation.
    
    Examples:
        worklog clean               # Clean today's entries
        worklog clean --date 2025-10-01  # Clean specific date
    """
    worklog = WorkLog()
    
    if date:
        # Validate date format
        try:
            datetime.strptime(date, "%Y-%m-%d")
            worklog.clean_date_worklog(date)
        except ValueError:
            console.print("❌ Invalid date format. Use YYYY-MM-DD", style="red")
            raise typer.Exit(1)
    else:
        worklog.clean_today_worklog()

@app.command("list", short_help="📋 List active tasks")
def list() -> None:
    """
    📋 List active tasks OR show today's log if none active.
    
    Smart display: shows active tasks table or today's work summary.
    """
    worklog = WorkLog()
    worklog.list_active_tasks()

@app.command()
def recent(
    count: int = typer.Option(10, "--count", "-c", help="Number of recent entries")
) -> None:
    """
    📊 Show recent completed entries.
    
    Display the most recent completed task entries with timestamps and durations.
    """
    worklog = WorkLog()
    worklog.show_recent_entries(count)

@app.command("today", short_help="📅 Show today's worklog")  
def today() -> None:
    """
    📅 Show today's worklog file.
    
    Display the human-readable daily log for today.
    """
    worklog = WorkLog()
    worklog.show_today_file()

@app.command("date", short_help="📅 Show worklog for specific date")
def date(
    date_str: str = typer.Argument(help="Date in YYYY-MM-DD format")
) -> None:
    """
    📅 Show worklog file for specific date.
    
    Display work activity for any historical date.
    """
    worklog = WorkLog()
    worklog.show_date_file(date_str)

if __name__ == "__main__":
    app()