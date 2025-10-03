"""
Drudge CLI - A comprehensive work time tracking tool.

This package provides a complete solution for tracking work time,
managing tasks, and generating reports with a clean, intuitive
command-line interface.

Key Features:
- Task time tracking with start/stop/pause/resume
- Automatic data persistence and backup
- Daily activity summaries and reports  
- Rich CLI interface with colors and formatting
- Configurable settings and preferences
- Data validation and error handling

Usage:
    from worklog import WorkLog, WorkLogConfig
    
    config = WorkLogConfig()
    worklog = WorkLog(config=config)
    worklog.start_task("My Task")
"""

from .config import WorkLogConfig
from .models import TaskEntry, PausedTask, WorkLogData
from .validators import WorkLogValidator
from .managers import WorkLog, BackupManager, DailyFileManager
from .cli import main

__version__ = "2.0.0"
__author__ = "Drudge Development Team"
__description__ = "Drudge CLI - A comprehensive work time tracking tool"

__all__ = [
    'WorkLog',
    'WorkLogConfig', 
    'TaskEntry',
    'PausedTask',
    'WorkLogData',
    'WorkLogValidator',
    'BackupManager',
    'DailyFileManager',
    'main'
]