#!/usr/bin/env python3
"""
Comprehensive Unit Tests for WorkLog CLI Tool

Test suite ensuring all functionality of the refactored worklog tool works correctly.
Covers dataclasses, time handling, task operations, session management, and CLI integration.
"""

import unittest
from unittest.mock import patch, mock_open, MagicMock
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from io import StringIO
import sys
from typer.testing import CliRunner

# Import the worklog module
from worklog import (
    TaskEntry, PausedTask, WorkLogData, WorkLog, app,
    console, requires_data, auto_save
)


class TestDataClasses(unittest.TestCase):
    """Test the dataclass structures used in the worklog system."""
    
    def test_task_entry_creation(self):
        """Test TaskEntry dataclass creation and serialization."""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)
        
        entry = TaskEntry(
            task="Test Task",
            start_time=start_time,
            end_time=end_time
        )
        
        self.assertEqual(entry.task, "Test Task")
        self.assertEqual(entry.start_time, start_time)
        self.assertEqual(entry.end_time, end_time)
    
    def test_task_entry_active(self):
        """Test TaskEntry with no end_time (active task)."""
        start_time = datetime.now()
        
        entry = TaskEntry(
            task="Active Task",
            start_time=start_time,
            end_time=None
        )
        
        self.assertEqual(entry.task, "Active Task")
        self.assertEqual(entry.start_time, start_time)
        self.assertIsNone(entry.end_time)
    
    def test_paused_task_creation(self):
        """Test PausedTask dataclass creation."""
        paused = PausedTask(
            task="Paused Task",
            total_duration_so_far="01:00:00",
            last_paused_at="2025-10-03T12:00:00"
        )
        
        self.assertEqual(paused.task, "Paused Task")
        self.assertEqual(paused.total_duration_so_far, "01:00:00")
        self.assertEqual(paused.last_paused_at, "2025-10-03T12:00:00")
    
    def test_worklog_data_creation(self):
        """Test WorkLogData dataclass with default values."""
        data = WorkLogData()
        
        self.assertEqual(data.entries, [])
        self.assertEqual(data.active_tasks, {})
        self.assertEqual(data.paused_tasks, [])
    
    def test_worklog_data_with_data(self):
        """Test WorkLogData with actual data."""
        entries = [TaskEntry("Task1", datetime.now(), None)]
        active = {"Task1": "2025-10-03T09:00:00"}
        paused = [PausedTask("Task2", "00:30:00", "2025-10-03T12:00:00")]
        
        data = WorkLogData(
            entries=entries,
            active_tasks=active,
            paused_tasks=paused
        )
        
        self.assertEqual(len(data.entries), 1)
        self.assertEqual(len(data.active_tasks), 1)
        self.assertEqual(len(data.paused_tasks), 1)


class TestWorkLogInitialization(unittest.TestCase):
    """Test WorkLog class initialization and directory management."""
    
    def setUp(self):
        """Set up temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_home = Path(self.temp_dir) / "test_home"
        self.test_home.mkdir()
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    @patch('worklog.Path.home')
    def test_worklog_initialization(self, mock_home):
        """Test WorkLog initialization creates proper directory structure."""
        mock_home.return_value = self.test_home
        
        # Mock the _load_data method to avoid file operations
        with patch.object(WorkLog, '_load_data', return_value=WorkLogData()):
            worklog = WorkLog()
            
            expected_dir = self.test_home / '.worklog'
            expected_file = expected_dir / 'worklog.json'
            
            self.assertEqual(worklog.worklog_dir, expected_dir)
            self.assertEqual(worklog.worklog_file, expected_file)
    
    @patch('worklog.Path.home')
    def test_ensure_directory_creation(self, mock_home):
        """Test that worklog directory is created if it doesn't exist."""
        mock_home.return_value = self.test_home
        
        with patch.object(WorkLog, '_load_data', return_value=WorkLogData()):
            worklog = WorkLog()
            worklog._ensure_directory()
            
            worklog_dir = self.test_home / '.worklog'
            self.assertTrue(worklog_dir.exists())


class TestTimeHandling(unittest.TestCase):
    """Test time parsing, formatting, and duration calculation functions."""
    
    def setUp(self):
        """Set up WorkLog instance for testing."""
        with patch.object(WorkLog, '_load_data', return_value=WorkLogData()):
            self.worklog = WorkLog()
    
    def test_parse_time_valid_formats(self):
        """Test parsing various valid time formats."""
        test_cases = [
            ("09:30", (9, 30)),
            ("14:45", (14, 45)),
            ("00:00", (0, 0)),
            ("23:59", (23, 59))
        ]
        
        for time_str, expected in test_cases:
            with self.subTest(time_str=time_str):
                result = self.worklog._parse_time(time_str)
                self.assertEqual(result, expected)
    
    def test_parse_time_invalid_formats(self):
        """Test parsing invalid time formats raises ValueError."""
        invalid_times = [
            "25:00",  # Invalid hour
            "12:60",  # Invalid minute
            "9:30",   # Missing leading zero
            "abc:def", # Non-numeric
            "12:",    # Missing minute
            ":30",    # Missing hour
            ""        # Empty string
        ]
        
        for invalid_time in invalid_times:
            with self.subTest(time_str=invalid_time):
                with self.assertRaises(ValueError):
                    self.worklog._parse_time(invalid_time)
    
    def test_format_display_time(self):
        """Test formatting datetime for display."""
        test_time = datetime(2025, 10, 3, 14, 30, 15)
        result = self.worklog._format_display_time(test_time)
        self.assertEqual(result, "2025-10-03 14:30:15")
    
    def test_format_duration_calculation(self):
        """Test duration calculation between two times."""
        start = datetime(2025, 10, 3, 9, 0, 0)
        end = datetime(2025, 10, 3, 10, 30, 45)
        
        result = self.worklog._format_duration(start, end)
        self.assertEqual(result, "01:30:45")
    
    def test_format_duration_negative(self):
        """Test duration calculation with future start time."""
        start = datetime(2025, 10, 3, 10, 0, 0)
        end = datetime(2025, 10, 3, 9, 0, 0)  # End before start
        
        result = self.worklog._format_duration(start, end)
        self.assertTrue(result.startswith("-"))
    
    @patch('worklog.datetime')
    def test_get_current_timestamp(self, mock_datetime):
        """Test getting current timestamp."""
        fixed_time = datetime(2025, 10, 3, 15, 30, 45)
        mock_datetime.now.return_value = fixed_time
        
        result = self.worklog._get_current_timestamp()
        self.assertEqual(result, fixed_time)


class TestTaskOperations(unittest.TestCase):
    """Test core task operations: start, end, toggle."""
    
    def setUp(self):
        """Set up WorkLog instance with mock data."""
        self.mock_data = WorkLogData()
        with patch.object(WorkLog, '_load_data', return_value=self.mock_data):
            self.worklog = WorkLog()
    
    @patch('worklog.datetime')
    def test_start_new_task(self, mock_datetime):
        """Test starting a new task."""
        fixed_time = datetime(2025, 10, 3, 9, 0, 0)
        mock_datetime.now.return_value = fixed_time
        
        # Mock the _save_data method
        with patch.object(self.worklog, '_save_data'):
            result = self.worklog.start_task("Test Task")
            
            self.assertTrue(result)
            self.assertIn("Test Task", self.worklog.data.active_tasks)
            self.assertEqual(self.worklog.data.active_tasks["Test Task"], fixed_time)
    
    def test_start_existing_active_task(self):
        """Test starting a task that's already active."""
        # Set up existing active task
        existing_time = datetime(2025, 10, 3, 8, 0, 0)
        self.worklog.data.active_tasks["Existing Task"] = existing_time
        
        with patch.object(self.worklog, '_save_data'):
            result = self.worklog.start_task("Existing Task")
            
            self.assertFalse(result)  # Should not start duplicate
    
    @patch('worklog.datetime')
    def test_end_active_task(self, mock_datetime):
        """Test ending an active task."""
        start_time = datetime(2025, 10, 3, 9, 0, 0)
        end_time = datetime(2025, 10, 3, 10, 0, 0)
        mock_datetime.now.return_value = end_time
        
        # Set up active task
        self.worklog.data.active_tasks["Test Task"] = start_time
        self.worklog.data.entries = [TaskEntry("Test Task", start_time, None)]
        
        with patch.object(self.worklog, '_save_data'):
            with patch.object(self.worklog, '_write_to_daily_file'):
                result = self.worklog.end_task("Test Task")
                
                self.assertTrue(result)
                self.assertNotIn("Test Task", self.worklog.data.active_tasks)
                # Check that entry was completed
                completed_entry = self.worklog.data.entries[0]
                self.assertEqual(completed_entry.end_time, end_time)
    
    def test_end_inactive_task(self):
        """Test trying to end a task that's not active."""
        with patch.object(self.worklog, '_save_data'):
            result = self.worklog.end_task("Nonexistent Task")
            
            self.assertFalse(result)
    
    @patch('worklog.datetime')
    def test_toggle_task_start_new(self, mock_datetime):
        """Test toggle behavior when starting a new task."""
        fixed_time = datetime(2025, 10, 3, 9, 0, 0)
        mock_datetime.now.return_value = fixed_time
        
        with patch.object(self.worklog, 'start_task', return_value=True) as mock_start:
            with patch.object(self.worklog, 'end_task') as mock_end:
                result = self.worklog.toggle_task("New Task")
                
                mock_start.assert_called_once_with("New Task", parallel=False, custom_time=None)
                mock_end.assert_not_called()
                self.assertTrue(result)
    
    def test_toggle_task_end_existing(self):
        """Test toggle behavior when ending an active task."""
        # Set up active task
        self.worklog.data.active_tasks["Active Task"] = datetime.now()
        
        with patch.object(self.worklog, 'start_task') as mock_start:
            with patch.object(self.worklog, 'end_task', return_value=True) as mock_end:
                result = self.worklog.toggle_task("Active Task")
                
                mock_start.assert_not_called()
                mock_end.assert_called_once_with("Active Task")
                self.assertTrue(result)


class TestSessionManagement(unittest.TestCase):
    """Test session management: pause, resume, stop all tasks."""
    
    def setUp(self):
        """Set up WorkLog instance with test data."""
        self.mock_data = WorkLogData()
        with patch.object(WorkLog, '_load_data', return_value=self.mock_data):
            self.worklog = WorkLog()
    
    @patch('worklog.datetime')
    def test_pause_all_tasks(self, mock_datetime):
        """Test pausing all active tasks."""
        pause_time = datetime(2025, 10, 3, 12, 0, 0)
        mock_datetime.now.return_value = pause_time
        
        # Set up active tasks
        task1_start = datetime(2025, 10, 3, 9, 0, 0)
        task2_start = datetime(2025, 10, 3, 10, 0, 0)
        self.worklog.data.active_tasks = {
            "Task 1": task1_start,
            "Task 2": task2_start
        }
        
        with patch.object(self.worklog, '_save_data'):
            with patch.object(self.worklog, '_calculate_total_duration', return_value="02:30:00"):
                self.worklog.pause_all_tasks()
                
                # Check that all tasks are moved to paused
                self.assertEqual(len(self.worklog.data.active_tasks), 0)
                self.assertEqual(len(self.worklog.data.paused_tasks), 2)
                
                # Verify paused task details
                paused_task1 = next(p for p in self.worklog.data.paused_tasks if p.task == "Task 1")
                self.assertEqual(paused_task1.original_start, task1_start)
                self.assertEqual(paused_task1.pause_time, pause_time)
    
    @patch('worklog.datetime')
    def test_resume_last_task(self, mock_datetime):
        """Test resuming the most recently paused task."""
        resume_time = datetime(2025, 10, 3, 13, 0, 0)
        mock_datetime.now.return_value = resume_time
        
        # Set up paused task
        pause_time = datetime(2025, 10, 3, 12, 0, 0)
        paused_task = PausedTask(
            task="Paused Task",
            original_start=datetime(2025, 10, 3, 9, 0, 0),
            pause_time=pause_time,
            accumulated_seconds=3600
        )
        self.worklog.data.paused_tasks = [paused_task]
        
        with patch.object(self.worklog, '_save_data'):
            result = self.worklog.resume_last_task()
            
            self.assertTrue(result)
            self.assertEqual(len(self.worklog.data.paused_tasks), 0)
            self.assertIn("Paused Task", self.worklog.data.active_tasks)
            self.assertEqual(self.worklog.data.active_tasks["Paused Task"], resume_time)
    
    def test_resume_no_paused_tasks(self):
        """Test resume when no tasks are paused."""
        with patch.object(self.worklog, '_save_data'):
            result = self.worklog.resume_last_task()
            
            self.assertFalse(result)
    
    @patch('worklog.datetime')
    def test_stop_all_tasks(self, mock_datetime):
        """Test stopping all active and paused tasks."""
        stop_time = datetime(2025, 10, 3, 17, 0, 0)
        mock_datetime.now.return_value = stop_time
        
        # Set up active tasks
        task_start = datetime(2025, 10, 3, 16, 0, 0)
        self.worklog.data.active_tasks = {"Active Task": task_start}
        self.worklog.data.entries = [TaskEntry("Active Task", task_start, None)]
        
        # Set up paused tasks
        paused_task = PausedTask("Paused Task", datetime.now(), datetime.now(), 1800)
        self.worklog.data.paused_tasks = [paused_task]
        
        with patch.object(self.worklog, '_save_data'):
            with patch.object(self.worklog, '_write_to_daily_file'):
                self.worklog.stop_all_tasks()
                
                # Verify all tasks are stopped
                self.assertEqual(len(self.worklog.data.active_tasks), 0)
                self.assertEqual(len(self.worklog.data.paused_tasks), 0)
                
                # Verify active task entry was completed
                completed_entry = self.worklog.data.entries[0]
                self.assertEqual(completed_entry.end_time, stop_time)


class TestDataPersistence(unittest.TestCase):
    """Test file operations, data loading/saving, and backup functionality."""
    
    def setUp(self):
        """Set up temporary directory for file operations testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_home = Path(self.temp_dir) / "test_home"
        self.test_home.mkdir()
        self.worklog_dir = self.test_home / '.worklog'
        self.worklog_file = self.worklog_dir / 'worklog.json'
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    @patch('worklog.Path.home')
    def test_save_and_load_data(self, mock_home):
        """Test saving and loading worklog data."""
        mock_home.return_value = self.test_home
        
        # Create test data
        test_data = WorkLogData(
            entries=[TaskEntry("Test Task", datetime.now(), None)],
            active_tasks={"Test Task": datetime.now()},
            paused_tasks=[]
        )
        
        # Create WorkLog instance and save data
        with patch.object(WorkLog, '_load_data', return_value=test_data):
            worklog = WorkLog()
            worklog.data = test_data
            worklog._save_data()
            
            # Verify file was created
            self.assertTrue(self.worklog_file.exists())
            
            # Load data and verify
            loaded_data = worklog._load_data()
            self.assertEqual(len(loaded_data.entries), 1)
            self.assertEqual(len(loaded_data.active_tasks), 1)
            self.assertEqual(len(loaded_data.paused_tasks), 0)
    
    @patch('worklog.Path.home')
    def test_load_empty_data(self, mock_home):
        """Test loading data when no file exists."""
        mock_home.return_value = self.test_home
        
        worklog = WorkLog()
        data = worklog._load_data()
        
        # Should return default empty data
        self.assertEqual(len(data.entries), 0)
        self.assertEqual(len(data.active_tasks), 0)
        self.assertEqual(len(data.paused_tasks), 0)
    
    @patch('worklog.Path.home')
    def test_migration_old_file(self, mock_home):
        """Test migration from old .worklog.json file."""
        mock_home.return_value = self.test_home
        
        # Create old file format
        old_file = self.test_home / '.worklog.json'
        test_data = {
            "entries": [],
            "active_tasks": {},
            "paused_tasks": []
        }
        
        self.worklog_dir.mkdir(exist_ok=True)
        with open(old_file, 'w') as f:
            json.dump(test_data, f)
        
        # Initialize WorkLog (should trigger migration)
        worklog = WorkLog()
        worklog._migrate_old_file()
        
        # Verify new file exists and old file is gone
        self.assertTrue(self.worklog_file.exists())
        self.assertFalse(old_file.exists())


class TestCLIIntegration(unittest.TestCase):
    """Test Typer CLI commands and short options functionality."""
    
    def setUp(self):
        """Set up CLI runner for testing."""
        self.runner = CliRunner()
    
    def test_help_command(self):
        """Test that help command works correctly."""
        result = self.runner.invoke(app, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Track work time on tasks", result.stdout)
    
    def test_task_command_help(self):
        """Test task command help shows short options."""
        result = self.runner.invoke(app, ["task", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("-pl,-p", result.stdout)  # Short options for parallel
        self.assertIn("-t", result.stdout)      # Short option for start-time
    
    def test_recent_command_help(self):
        """Test recent command help shows count option."""
        result = self.runner.invoke(app, ["recent", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("-c", result.stdout)      # Short option for count
    
    def test_start_command_help(self):
        """Test start command help shows time option."""
        result = self.runner.invoke(app, ["start", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("-t", result.stdout)      # Short option for start-time
    
    @patch('worklog.WorkLog')
    def test_task_command_execution(self, mock_worklog_class):
        """Test task command execution with mocked WorkLog."""
        mock_instance = MagicMock()
        mock_worklog_class.return_value = mock_instance
        mock_instance.toggle_task.return_value = True
        
        result = self.runner.invoke(app, ["task", "Test Task"])
        self.assertEqual(result.exit_code, 0)
        mock_instance.toggle_task.assert_called_once_with("Test Task", parallel=False, custom_time=None)
    
    @patch('worklog.WorkLog')
    def test_task_command_with_short_options(self, mock_worklog_class):
        """Test task command with short options."""
        mock_instance = MagicMock()
        mock_worklog_class.return_value = mock_instance
        mock_instance.toggle_task.return_value = True
        
        # Test with parallel short option
        result = self.runner.invoke(app, ["task", "Test Task", "-p"])
        self.assertEqual(result.exit_code, 0)
        mock_instance.toggle_task.assert_called_with("Test Task", parallel=True, custom_time=None)
        
        # Test with time short option
        result = self.runner.invoke(app, ["task", "Test Task", "-t", "14:30"])
        self.assertEqual(result.exit_code, 0)
        mock_instance.toggle_task.assert_called_with("Test Task", parallel=False, custom_time="14:30")


class TestDecorators(unittest.TestCase):
    """Test custom decorators: requires_data and auto_save."""
    
    def test_requires_data_decorator(self):
        """Test that requires_data decorator loads data when needed."""
        # Create a mock class to test the decorator
        class MockWorkLog:
            def __init__(self):
                pass
            
            def _load_data(self):
                return WorkLogData()
            
            @requires_data
            def test_method(self):
                return "success"
        
        mock_instance = MockWorkLog()
        
        # Call decorated method
        result = mock_instance.test_method()
        
        self.assertEqual(result, "success")
        self.assertIsNotNone(mock_instance._data)
    
    def test_auto_save_decorator(self):
        """Test that auto_save decorator calls _save_data after method execution."""
        # Create a mock class to test the decorator
        class MockWorkLog:
            def __init__(self):
                self.save_called = False
            
            def _save_data(self):
                self.save_called = True
            
            @auto_save
            def test_method(self):
                return "success"
        
        mock_instance = MockWorkLog()
        
        # Call decorated method
        result = mock_instance.test_method()
        
        self.assertEqual(result, "success")
        self.assertTrue(mock_instance.save_called)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)