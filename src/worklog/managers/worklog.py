"""
Core WorkLog management class.

This module contains the main WorkLog class that orchestrates all
time tracking functionality and integrates with other components.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Any, Union
from contextlib import contextmanager
from functools import lru_cache
import logging

from rich.console import Console
from rich.table import Table

from ..models import TaskEntry, PausedTask, WorkLogData
from ..config import WorkLogConfig
from ..validators import WorkLogValidator
from ..utils.decorators import requires_data, auto_save
from .backup import BackupManager
from .daily_file import DailyFileManager

# Initialize rich console for beautiful output
console = Console()
logger = logging.getLogger(__name__)


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
        self.backup_manager = BackupManager()
        
        # Handle configurable worklog directory path
        if hasattr(self.config, 'worklog_dir') and self.config.worklog_dir:
            self.worklog_dir = Path(self.config.worklog_dir)
        else:
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
                logger.error(f"Migration failed: {e}")
                console.print(f"⚠️ Migration failed: {e}", style="yellow")
    
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
    
    # ============================================================================
    # Time and Utility Methods
    # ============================================================================
    
    @staticmethod
    def _get_current_timestamp() -> str:
        """
        Get current timestamp in ISO format.
        
        Returns:
            str: Current timestamp in ISO format for consistency
        """
        return datetime.now().isoformat()
    
    @lru_cache(maxsize=128)
    def _format_display_time(self, timestamp: str) -> str:
        """
        Format ISO timestamp for human-readable display.
        
        Cached method for efficient timestamp formatting throughout the system.
        
        Args:
            timestamp: ISO format timestamp string
            
        Returns:
            str: Formatted timestamp for display
        """
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime(self.config.display_time_format)
    
    def _format_duration(self, start_time: str, end_time: str) -> str:
        """
        Calculate and format duration between two timestamps.
        
        Args:
            start_time: ISO timestamp string for start
            end_time: ISO timestamp string for end
            
        Returns:
            str: Formatted duration in HH:MM:SS format
        """
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time)
        
        duration = end_dt - start_dt
        if duration.total_seconds() < 0:
            return "00:00:00"  # Handle negative durations gracefully
        
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def _get_timestamp(self, custom_time: Optional[str]) -> str:
        """
        Get timestamp for task operations, with optional custom time.
        
        Args:
            custom_time: Optional HH:MM format time string
            
        Returns:
            str: ISO timestamp string
        """
        if custom_time:
            return self._parse_custom_time(custom_time)
        return self._get_current_timestamp()
    
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
    
    def _get_daily_file_path(self, date_str: Optional[str] = None) -> Path:
        """
        Get path to daily log file for a specific date.
        
        Args:
            date_str: Optional date string (YYYY-MM-DD), defaults to today
            
        Returns:
            Path: Path to the daily log file
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        daily_dir = self.worklog_dir / "daily"
        daily_dir.mkdir(exist_ok=True)
        return daily_dir / f"{date_str}.txt"
    
    def _update_daily_file(self, task_name: str, action: str, timestamp: str, duration: Optional[str] = None) -> None:
        """
        Update daily human-readable log file with task activity.
        
        Uses the DailyFileManager for consistent formatting and chronological ordering.
        
        Args:
            task_name: Name of the task being logged
            action: Type of action ('start', 'end', 'pause', 'resume', 'completed')
            timestamp: ISO timestamp of the action
            duration: Optional duration string for completed tasks
        """
        daily_file = self._get_daily_file_path()
        entry = self.daily_file_manager.format_entry(task_name, action, timestamp, duration)
        self.daily_file_manager.add_entry_chronologically(daily_file, entry)
    
    # ============================================================================
    # Task Management Methods  
    # ============================================================================
    
    @auto_save
    def start_task(self, task_name: str, custom_time: str = None, force: bool = False) -> bool:
        """
        Start a new task or resume an existing one.
        
        Handles task validation, active task management, and proper time tracking
        with enhanced user experience and comprehensive error handling.
        
        Args:
            task_name: Name of the task to start
            custom_time: Optional HH:MM format time (e.g., "09:30") to use instead of current time
            force: If True, automatically ends any currently active tasks
            
        Returns:
            bool: True if task started successfully, False otherwise
            
        Raises:
            ValueError: If task name is invalid or time format is wrong
        """
        try:
            # Validate inputs using centralized validation
            if task_name is None:
                raise ValueError("Task name cannot be None")
            task_name = WorkLogValidator.validate_task_name(task_name)
            timestamp = self._get_timestamp(custom_time)
            
            # Display formatted time for user confirmation
            display_time = self._format_display_time(timestamp)
            
            # Check for existing active tasks
            if self.data.active_tasks and not force:
                active_list = ', '.join(self.data.active_tasks.keys())
                console.print(
                    f"⚠️ Active tasks: {active_list}\n"
                    "💡 Use 'worklog end <task>' first or --force to auto-end",
                    style="yellow"
                )
                return False
            
            # Auto-end active tasks if force is enabled
            if force and self.data.active_tasks:
                for active_task in list(self.data.active_tasks.keys()):
                    console.print(f"🏁 Auto-ending: {active_task}")
                    self.end_task(active_task, timestamp=timestamp)
            
            # Check if task is currently paused (resume it)
            paused_task = next(
                (task for task in self.data.paused_tasks if task.task == task_name), 
                None
            )
            
            if paused_task:
                # Resume paused task
                self.data.paused_tasks.remove(paused_task)
                self.data.active_tasks[task_name] = timestamp
                console.print(f"▶️ Resumed '{task_name}' at {display_time}")
                logger.info(f"Task resumed: {task_name} at {timestamp}")
                self._update_daily_file(task_name, "resume", timestamp)
                return True
            
            # Start new task
            self.data.active_tasks[task_name] = timestamp
            
            # Add to recent tasks (maintain max size)
            if task_name not in self.data.recent_tasks:
                self.data.recent_tasks.insert(0, task_name)
                if len(self.data.recent_tasks) > self.config.max_recent_tasks:
                    self.data.recent_tasks = self.data.recent_tasks[:self.config.max_recent_tasks]
            
            console.print(f"🚀 Started '{task_name}' at {display_time}")
            logger.info(f"Task started: {task_name} at {timestamp}")
            self._update_daily_file(task_name, "start", timestamp)
            return True
            
        except ValueError as e:
            console.print(f"❌ Invalid input: {e}", style="red")
            logger.warning(f"Task start failed - validation error: {e}")
            return False
        except Exception as e:
            console.print(f"❌ Failed to start task: {e}", style="red")
            logger.error(f"Unexpected error starting task {task_name}: {e}")
            return False
    
    @auto_save  
    def end_task(self, task_name: str, custom_time: str = None, timestamp: str = None) -> bool:
        """
        End an active task and record its completion.
        
        Creates a task entry with calculated duration and updates all tracking
        systems (JSON database, daily files, active tasks list).
        
        Args:
            task_name: Name of the task to end
            custom_time: Optional HH:MM format time for custom end time
            timestamp: Internal parameter for precise timestamp (used by auto-end)
            
        Returns:
            bool: True if task ended successfully, False otherwise
        """
        try:
            if task_name is None:
                raise ValueError("Task name cannot be None")
            task_name = WorkLogValidator.validate_task_name(task_name)
            
            # Check if task is active
            if task_name not in self.data.active_tasks:
                available_tasks = ', '.join(self.data.active_tasks.keys()) if self.data.active_tasks else 'No active tasks'
                console.print(
                    f"⚠️ '{task_name}' is not active\n"
                    f"📋 Active tasks: {available_tasks}",
                    style="yellow"
                )
                return False
            
            # Get end timestamp (either provided internally or from user input)
            end_timestamp = timestamp or self._get_timestamp(custom_time)
            
            # Find the start time for this task
            start_time = self._find_task_start_time(task_name)
            if not start_time:
                console.print(f"⚠️ Cannot find start time for '{task_name}'", style="yellow")
                return False
            
            # Calculate duration
            duration = self._format_duration(start_time, end_timestamp)
            display_end_time = self._format_display_time(end_timestamp)
            
            # Create task entry
            entry = TaskEntry(
                task=task_name,
                start_time=start_time,
                end_time=end_timestamp,
                duration=duration
            )
            
            # Update data structures
            self.data.entries.append(entry)
            del self.data.active_tasks[task_name]
            
            console.print(f"🏁 Completed '{task_name}' at {display_end_time} (Duration: {duration})")
            logger.info(f"Task completed: {task_name}, duration: {duration}")
            
            # Update daily file with completion info
            self._update_daily_file(task_name, "completed", end_timestamp, duration)
            return True
            
        except ValueError as e:
            console.print(f"❌ Invalid input: {e}", style="red")
            logger.warning(f"Task end failed - validation error: {e}")
            return False
        except Exception as e:
            console.print(f"❌ Failed to end task: {e}", style="red")
            logger.error(f"Unexpected error ending task {task_name}: {e}")
            return False
    
    @auto_save
    def pause_task(self, task_name: str, custom_time: str = None) -> bool:
        """
        Pause an active task for later resumption.
        
        Moves task from active to paused state while preserving start time
        for accurate duration calculation when resumed and completed.
        
        Args:
            task_name: Name of the task to pause
            custom_time: Optional HH:MM format time for custom pause time
            
        Returns:
            bool: True if task paused successfully, False otherwise
        """
        try:
            if task_name is None:
                raise ValueError("Task name cannot be None")
            task_name = WorkLogValidator.validate_task_name(task_name)
            timestamp = self._get_timestamp(custom_time)
            
            if task_name not in self.data.active_tasks:
                console.print(f"⚠️ '{task_name}' is not currently active", style="yellow")
                return False
            
            # Find start time
            start_time = self._find_task_start_time(task_name)
            if not start_time:
                console.print(f"⚠️ Cannot find start time for '{task_name}'", style="yellow")
                return False
            
            # Create paused task entry
            paused_task = PausedTask(task=task_name, start_time=start_time)
            
            # Update data structures
            self.data.paused_tasks.append(paused_task)
            del self.data.active_tasks[task_name]
            
            display_time = self._format_display_time(timestamp)
            console.print(f"⏸️ Paused '{task_name}' at {display_time}")
            logger.info(f"Task paused: {task_name} at {timestamp}")
            
            self._update_daily_file(task_name, "pause", timestamp)
            return True
            
        except ValueError as e:
            console.print(f"❌ Invalid input: {e}", style="red")
            return False
        except Exception as e:
            console.print(f"❌ Failed to pause task: {e}", style="red")
            logger.error(f"Error pausing task {task_name}: {e}")
            return False
    
    def _find_task_start_time(self, task_name: str) -> Optional[str]:
        """
        Find the most recent start time for an active task.
        
        Uses the active_tasks dict to get the start time directly, or falls back
        to paused task records for accurate duration calculation.
        
        Args:
            task_name: Name of the task to find start time for
            
        Returns:
            Optional[str]: ISO timestamp of task start, or None if not found
        """
        # First check active tasks dict (most direct)
        if task_name in self.data.active_tasks:
            return self.data.active_tasks[task_name]
        
        # Then check if there's a paused task record 
        paused_task = next(
            (task for task in self.data.paused_tasks if task.task == task_name), 
            None
        )
        if paused_task:
            return paused_task.start_time
        
        # Fallback: estimate from recent entries or current time
        logger.warning(f"Start time not found for {task_name}, using current session estimate")
        
        # Look for recent completed entries of the same task to estimate session length
        recent_entries = [e for e in self.data.entries[-10:] if e.task == task_name]
        if recent_entries:
            # Use typical task duration as fallback
            latest_entry = recent_entries[-1]
            if latest_entry.duration:
                # This is a simple fallback - in practice, we'd track active starts better
                return datetime.now().isoformat()
        
        # Ultimate fallback: assume task started now (will result in 0 duration)
        return self._get_current_timestamp()
    
    def resume_task(self, task_name: str, custom_time: str = None) -> bool:
        """
        Resume a previously paused task.
        
        This is a convenience method that calls start_task, which handles
        paused task resumption automatically.
        
        Args:
            task_name: Name of the task to resume
            custom_time: Optional HH:MM format time for custom resume time
            
        Returns:
            bool: True if task resumed successfully, False otherwise
        """
        return self.start_task(task_name, custom_time)
    
    # ============================================================================
    # Status and Listing Methods
    # ============================================================================
    
    @requires_data
    def show_status(self) -> None:
        """
        Display current work status including active and paused tasks.
        
        Shows a comprehensive overview of the current session state with
        active tasks, paused tasks, and recent activity summary.
        """
        if not self.data.active_tasks and not self.data.paused_tasks:
            console.print("😴 No active or paused tasks", style="dim")
            return
        
        # Show active tasks
        if self.data.active_tasks:
            console.print("🚀 Active Tasks:", style="bold green")
            for task_name, start_time in self.data.active_tasks.items():
                # Calculate runtime for active tasks
                current_duration = self._format_duration(start_time, self._get_current_timestamp())
                console.print(f"  • {task_name} (Running: {current_duration})")
        
        # Show paused tasks
        if self.data.paused_tasks:
            console.print("\n⏸️ Paused Tasks:", style="bold yellow")
            for task in self.data.paused_tasks:
                console.print(f"  • {task.task}")
        
        # Show recent activity count
        if self.data.entries:
            today = datetime.now().strftime("%Y-%m-%d")
            today_entries = [e for e in self.data.entries if e.start_time.startswith(today)]
            if today_entries:
                console.print(f"\n📊 Completed today: {len(today_entries)} tasks")
    
    @requires_data
    def list_recent_tasks(self, limit: int = None) -> None:
        """
        Display recent task names for quick reference and reuse.
        
        Args:
            limit: Optional limit on number of tasks to show
        """
        if not self.data.recent_tasks:
            console.print("📝 No recent tasks found", style="dim")
            return
        
        display_limit = min(limit or self.config.max_recent_tasks, len(self.data.recent_tasks))
        console.print("📝 Recent Tasks:", style="bold")
        
        for i, task in enumerate(self.data.recent_tasks[:display_limit], 1):
            console.print(f"  {i}. {task}")
    
    @requires_data
    def list_entries(self, date: str = None, limit: int = None, task_filter: str = None) -> None:
        """
        List completed task entries with optional filtering.
        
        Args:
            date: Optional date filter (YYYY-MM-DD format)
            limit: Optional limit on number of entries to show
            task_filter: Optional task name filter (partial match)
        """
        entries = self.data.entries.copy()
        
        # Apply date filter
        if date:
            try:
                WorkLogValidator.validate_date_format(date)
                entries = [e for e in entries if e.start_time.startswith(date)]
            except ValueError as e:
                console.print(f"❌ Invalid date format: {e}", style="red")
                return
        
        # Apply task name filter
        if task_filter:
            entries = [e for e in entries if task_filter.lower() in e.task.lower()]
        
        # Apply limit
        if limit:
            entries = entries[-limit:]  # Show most recent if limited
        
        if not entries:
            filter_desc = f" (filtered: date={date}, task={task_filter})" if (date or task_filter) else ""
            console.print(f"📋 No entries found{filter_desc}", style="dim")
            return
        
        # Display entries
        console.print(f"📋 Task Entries ({len(entries)} found):", style="bold")
        
        for entry in entries:
            start_display = self._format_display_time(entry.start_time)
            end_display = self._format_display_time(entry.end_time)
            console.print(
                f"  • {entry.task}\n"
                f"    {start_display} → {end_display} ({entry.duration})"
            )
    
    @requires_data
    def show_daily_summary(self, date: str = None) -> None:
        """
        Show summary of work done on a specific day.
        
        Args:
            date: Optional date (YYYY-MM-DD), defaults to today
        """
        target_date = date or datetime.now().strftime("%Y-%m-%d")
        
        # Validate date format
        try:
            WorkLogValidator.validate_date_format(target_date)
        except ValueError as e:
            console.print(f"❌ Invalid date format: {e}", style="red")
            return
        
        # Filter entries for the date
        day_entries = [e for e in self.data.entries if e.start_time.startswith(target_date)]
        
        if not day_entries:
            console.print(f"📅 No tasks completed on {target_date}", style="dim")
            return
        
        # Calculate total time
        total_seconds = 0
        for entry in day_entries:
            start_dt = datetime.fromisoformat(entry.start_time)
            end_dt = datetime.fromisoformat(entry.end_time)
            total_seconds += (end_dt - start_dt).total_seconds()
        
        total_hours = total_seconds // 3600
        total_minutes = (total_seconds % 3600) // 60
        
        # Display summary
        console.print(f"📅 Daily Summary for {target_date}", style="bold")
        console.print(f"📊 Total: {len(day_entries)} tasks, {total_hours:.0f}h {total_minutes:.0f}m")
        
        # Group by task name
        task_durations = {}
        for entry in day_entries:
            if entry.task not in task_durations:
                task_durations[entry.task] = 0
            
            start_dt = datetime.fromisoformat(entry.start_time)
            end_dt = datetime.fromisoformat(entry.end_time)
            task_durations[entry.task] += (end_dt - start_dt).total_seconds()
        
        # Display task breakdown
        console.print("\n📋 Tasks:")
        for task_name, seconds in sorted(task_durations.items(), key=lambda x: x[1], reverse=True):
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            console.print(f"  • {task_name}: {hours:.0f}h {minutes:.0f}m")