"""
Configuration management for WorkLog CLI Tool.

This module provides centralized configuration with sensible defaults
and customization options for the worklog system.
"""

from dataclasses import dataclass


@dataclass
class WorkLogConfig:
    """
    Configuration settings for WorkLog with sensible defaults.
    
    Centralizes all configurable options for the worklog system,
    allowing users to customize behavior without code changes.
    
    Attributes:
        worklog_dir_name: Name of the worklog directory
        worklog_dir: Optional override for custom directory path (for testing)
        date_format: Date format string for parsing and display
        time_format: Time format string for parsing user input
        display_time_format: Format for displaying timestamps to users
        max_recent_tasks: Maximum number of recent tasks to remember
        backup_enabled: Whether to create backups before destructive operations
        auto_save: Whether to automatically save after each operation
        max_backups: Maximum number of backup files to retain
    """
    worklog_dir_name: str = '.worklog'
    worklog_dir: str = None  # Optional override for custom directory path
    date_format: str = "%Y-%m-%d"
    time_format: str = "%H:%M"
    display_time_format: str = "%Y-%m-%d %H:%M:%S"
    max_recent_tasks: int = 10
    backup_enabled: bool = True
    auto_save: bool = True
    max_backups: int = 5