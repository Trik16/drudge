#!/usr/bin/env python3
"""
Updated Unit Tests for Refactored WorkLog CLI Tool

Test suite for the improved worklog tool with new architecture:
- WorkLogValidator for centralized validation
- WorkLogConfig for configuration management
- BackupManager and DailyFileManager for specialized operations
- Enhanced error handling and logging
"""

import unittest
from unittest.mock import patch, mock_open, MagicMock, PropertyMock
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import os
from typer.testing import CliRunner

# Import the refactored worklog components
from src.worklog import (
    TaskEntry, PausedTask, WorkLogData, WorkLog, WorkLogConfig, WorkLogValidator,
    BackupManager, DailyFileManager
)
from src.worklog.cli import app
from rich.console import Console

console = Console()


class TestWorkLogValidator(unittest.TestCase):
    """Test the centralized validation logic."""
    
    def setUp(self):
        self.validator = WorkLogValidator()
        self.config = WorkLogConfig()
    
    def test_validate_date_format_valid(self):
        """Test valid date formats pass validation."""
        # Should not raise exception
        self.validator.validate_date_format("2023-12-31", self.config)
        self.validator.validate_date_format("2023-01-01", self.config)
        
    def test_validate_date_format_invalid(self):
        """Test invalid date formats raise ValueError."""
        with self.assertRaises(ValueError):
            self.validator.validate_date_format("31-12-2023", self.config)
        with self.assertRaises(ValueError):
            self.validator.validate_date_format("invalid-date", self.config)
    
    def test_validate_time_format_valid(self):
        """Test valid time formats pass validation."""
        # Should return (hours, minutes) tuple
        hours, minutes = self.validator.validate_time_format("14:30")
        self.assertEqual(hours, 14)
        self.assertEqual(minutes, 30)
        
        hours, minutes = self.validator.validate_time_format("09:00")
        self.assertEqual(hours, 9)
        self.assertEqual(minutes, 0)
    
    def test_validate_time_format_invalid(self):
        """Test invalid time formats raise ValueError."""
        invalid_times = ["25:00", "12:60", "abc:def", "12:", ":30", ""]
        for invalid_time in invalid_times:
            with self.assertRaises(ValueError):
                self.validator.validate_time_format(invalid_time)
    
    def test_validate_task_name_valid(self):
        """Test valid task names pass validation."""
        # Should not raise exception
        self.validator.validate_task_name("Valid Task Name")
        self.validator.validate_task_name("Task-With-Dashes")
    
    def test_validate_task_name_invalid(self):
        """Test invalid task names raise ValueError."""
        with self.assertRaises(ValueError):
            self.validator.validate_task_name("")  # Empty
        with self.assertRaises(ValueError):
            self.validator.validate_task_name("   ")  # Only whitespace
        with self.assertRaises(ValueError):
            self.validator.validate_task_name("a" * 101)  # Too long


class TestWorkLogConfig(unittest.TestCase):
    """Test configuration management."""
    
    def test_default_config_values(self):
        """Test default configuration values are sensible."""
        config = WorkLogConfig()
        self.assertEqual(config.worklog_dir_name, '.worklog')
        self.assertEqual(config.date_format, "%Y-%m-%d")
        self.assertEqual(config.time_format, "%H:%M")
        self.assertTrue(config.backup_enabled)
        self.assertTrue(config.auto_save)
    
    def test_custom_config_values(self):
        """Test custom configuration values work correctly."""
        config = WorkLogConfig(
            worklog_dir_name='custom_worklog',
            max_recent_tasks=5,
            backup_enabled=False
        )
        self.assertEqual(config.worklog_dir_name, 'custom_worklog')
        self.assertEqual(config.max_recent_tasks, 5)
        self.assertFalse(config.backup_enabled)


class TestDataClasses(unittest.TestCase):
    """Test the dataclass structures used in the worklog system."""
    
    def test_task_entry_creation(self):
        """Test TaskEntry dataclass creation."""
        entry = TaskEntry(
            task="Test Task",
            start_time="2023-12-31T14:30:00",
            end_time="2023-12-31T15:30:00",
            duration="01:00:00"
        )
        
        self.assertEqual(entry.task, "Test Task")
        self.assertEqual(entry.start_time, "2023-12-31T14:30:00")
        self.assertEqual(entry.end_time, "2023-12-31T15:30:00")
        self.assertEqual(entry.duration, "01:00:00")
    
    def test_task_entry_active(self):
        """Test TaskEntry with no end_time (active task)."""
        entry = TaskEntry(
            task="Active Task",
            start_time="2023-12-31T14:30:00"
        )
        
        self.assertEqual(entry.task, "Active Task")
        self.assertEqual(entry.start_time, "2023-12-31T14:30:00")
        self.assertIsNone(entry.end_time)
        self.assertIsNone(entry.duration)
    
    def test_paused_task_creation(self):
        """Test PausedTask dataclass creation."""
        paused_task = PausedTask(
            task="Paused Task",
            start_time="2023-12-31T14:30:00"
        )
        
        self.assertEqual(paused_task.task, "Paused Task")
        self.assertEqual(paused_task.start_time, "2023-12-31T14:30:00")
    
    def test_worklog_data_creation(self):
        """Test WorkLogData dataclass with default values."""
        data = WorkLogData()
        
        self.assertEqual(data.entries, [])
        self.assertEqual(data.active_tasks, {})
        self.assertEqual(data.paused_tasks, [])
        self.assertEqual(data.recent_tasks, [])
    
    def test_worklog_data_with_data(self):
        """Test WorkLogData with actual data."""
        entry = TaskEntry(task="Test", start_time="2023-12-31T14:30:00")
        paused = PausedTask(task="Paused", start_time="2023-12-31T13:00:00")
        
        data = WorkLogData(
            entries=[entry],
            active_tasks={"Active Task": "2023-12-31T14:00:00"},
            paused_tasks=[paused],
            recent_tasks=["Recent Task"]
        )
        
        self.assertEqual(len(data.entries), 1)
        self.assertEqual(len(data.active_tasks), 1)
        self.assertEqual(len(data.paused_tasks), 1)
        self.assertEqual(len(data.recent_tasks), 1)


class TestWorkLogInitialization(unittest.TestCase):
    """Test WorkLog initialization and directory creation."""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_home = os.environ.get('HOME')
        os.environ['HOME'] = self.test_dir
    
    def tearDown(self):
        if self.original_home:
            os.environ['HOME'] = self.original_home
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_worklog_initialization(self):
        """Test WorkLog initialization creates proper directory structure."""
        worklog = WorkLog()
        
        self.assertTrue(worklog.worklog_dir.exists())
        self.assertEqual(worklog.worklog_dir.name, '.worklog')
        self.assertTrue(worklog.worklog_file.name.endswith('.json'))
    
    def test_ensure_directory_creation(self):
        """Test that worklog directory is created if it doesn't exist."""
        worklog_dir = Path(self.test_dir) / '.worklog'
        self.assertFalse(worklog_dir.exists())
        
        worklog = WorkLog()
        self.assertTrue(worklog.worklog_dir.exists())


class TestTimeHandling(unittest.TestCase):
    """Test time parsing and formatting functionality."""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_home = os.environ.get('HOME')
        os.environ['HOME'] = self.test_dir
        self.worklog = WorkLog()
    
    def tearDown(self):
        if self.original_home:
            os.environ['HOME'] = self.original_home
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_get_current_timestamp(self):
        """Test getting current timestamp returns ISO format."""
        with patch('src.worklog.managers.worklog.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 10, 3, 15, 30, 45)
            mock_datetime.fromisoformat = datetime.fromisoformat
            
            result = WorkLog._get_current_timestamp()
            self.assertEqual(result, '2025-10-03T15:30:45')
    
    def test_format_display_time(self):
        """Test formatting datetime for display."""
        timestamp = "2023-12-31T14:30:00"
        result = self.worklog._format_display_time(timestamp)
        self.assertEqual(result, "2023-12-31 14:30:00")
    
    def test_format_duration_calculation(self):
        """Test duration calculation between two times."""
        start = "2023-12-31T14:30:00"
        end = "2023-12-31T15:45:30"
        result = self.worklog._format_duration(start, end)
        self.assertEqual(result, "01:15:30")
    
    def test_parse_custom_time_valid_formats(self):
        """Test parsing various valid time formats."""
        valid_times = ["09:30", "14:45", "00:00", "23:59"]
        for time_str in valid_times:
            result = WorkLog._parse_custom_time(time_str)
            self.assertIsInstance(result, str)
            # Should be valid ISO timestamp
            datetime.fromisoformat(result)


class TestTaskOperations(unittest.TestCase):
    """Test core task management operations."""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_home = os.environ.get('HOME')
        os.environ['HOME'] = self.test_dir
        self.worklog = WorkLog()
    
    def tearDown(self):
        if self.original_home:
            os.environ['HOME'] = self.original_home
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @patch('src.worklog.managers.worklog.WorkLog._get_current_timestamp')
    def test_start_new_task(self, mock_timestamp):
        """Test starting a new task."""
        mock_timestamp.return_value = '2025-10-03T09:00:00'
        
        self.worklog.start_task("Test Task")
        
        self.assertIn("Test Task", self.worklog.data.active_tasks)
        self.assertEqual(self.worklog.data.active_tasks["Test Task"], '2025-10-03T09:00:00')
    
    def test_start_existing_active_task(self):
        """Test starting a task that's already active."""
        self.worklog.data.active_tasks["Existing Task"] = '2025-10-03T08:00:00'
        
        # Should show warning message and not change anything
        result = self.worklog.start_task("Existing Task")
        self.assertFalse(result)  # Should return False for already active task
    
    @patch('src.worklog.managers.worklog.WorkLog._get_current_timestamp')
    def test_end_active_task(self, mock_timestamp):
        """Test ending an active task."""
        mock_timestamp.return_value = '2025-10-03T10:00:00'
        
        # Set up an active task (end_task will create the entry)
        self.worklog.data.active_tasks["Active Task"] = '2025-10-03T09:00:00'
        
        result = self.worklog.end_task("Active Task")
        
        # Task should be removed from active tasks
        self.assertNotIn("Active Task", self.worklog.data.active_tasks)
        self.assertTrue(result)  # Should return True for successful end
        
        # Task entry should be created
        self.assertEqual(len(self.worklog.data.entries), 1)
        updated_entry = self.worklog.data.entries[0]
        self.assertEqual(updated_entry.task, "Active Task")
        self.assertEqual(updated_entry.start_time, '2025-10-03T09:00:00')
        self.assertEqual(updated_entry.end_time, '2025-10-03T10:00:00')
        self.assertEqual(updated_entry.duration, "01:00:00")
    
    def test_end_inactive_task(self):
        """Test trying to end a task that's not active."""
        result = self.worklog.end_task("Nonexistent Task")
        self.assertFalse(result)  # Should return False for inactive task


class TestSessionManagement(unittest.TestCase):
    """Test pause/resume and session management functionality."""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_home = os.environ.get('HOME')
        os.environ['HOME'] = self.test_dir
        self.worklog = WorkLog()
    
    def tearDown(self):
        if self.original_home:
            os.environ['HOME'] = self.original_home
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @patch('worklog.WorkLog._get_current_timestamp')
    def test_pause_all_tasks(self, mock_timestamp):
        """Test pausing active tasks."""
        mock_timestamp.return_value = '2025-10-03T10:00:00'
        
        # Set up an active task
        task_start = '2025-10-03T09:00:00'
        self.worklog.data.active_tasks = {
            "Task 1": task_start
        }
        
        # Pause the task
        result = self.worklog.pause_task("Task 1")
        
        self.assertTrue(result)
        # Active tasks should be cleared
        self.assertNotIn("Task 1", self.worklog.data.active_tasks)
        
        # Should have paused task
        self.assertEqual(len(self.worklog.data.paused_tasks), 1)
        
        # Check paused task structure
        paused_task = self.worklog.data.paused_tasks[0]
        self.assertEqual(paused_task.task, "Task 1")
        self.assertEqual(paused_task.start_time, task_start)
    
    def test_resume_no_paused_tasks(self):
        """Test resume when task is not paused - should start it as new."""
        result = self.worklog.resume_task("Nonexistent Task")
        # resume_task calls start_task, so it will succeed and start a new task
        self.assertTrue(result)
        self.assertIn("Nonexistent Task", self.worklog.data.active_tasks)
    
    @patch('worklog.WorkLog._get_current_timestamp')
    def test_resume_last_task(self, mock_timestamp):
        """Test resuming a paused task."""
        mock_timestamp.return_value = '2025-10-03T11:00:00'
        
        # Set up a paused task
        paused_task = PausedTask(
            task="Paused Task",
            start_time='2025-10-03T09:00:00'
        )
        self.worklog.data.paused_tasks = [paused_task]
        
        result = self.worklog.resume_task("Paused Task")
        
        self.assertTrue(result)
        self.assertEqual(len(self.worklog.data.paused_tasks), 0)
        self.assertIn("Paused Task", self.worklog.data.active_tasks)


class TestCLIIntegration(unittest.TestCase):
    """Test CLI command integration."""
    
    def setUp(self):
        self.runner = CliRunner()
        self.test_dir = tempfile.mkdtemp()
        self.original_home = os.environ.get('HOME')
        os.environ['HOME'] = self.test_dir
    
    def tearDown(self):
        if self.original_home:
            os.environ['HOME'] = self.original_home
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_help_command(self):
        """Test that help command works correctly."""
        result = self.runner.invoke(app, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Drudge CLI", result.stdout)
        self.assertIn("work time tracking", result.stdout)
    
    def test_task_command_help(self):
        """Test start command help shows options."""
        result = self.runner.invoke(app, ["start", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Start a new task", result.stdout)


if __name__ == '__main__':
    # Run all tests
    unittest.main()