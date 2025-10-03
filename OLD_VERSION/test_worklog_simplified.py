#!/usr/bin/env python3
"""
Simplified Unit Tests for WorkLog CLI Tool

Focused test suite ensuring core functionality of the refactored worklog tool works correctly.
Tests critical paths without mocking internal implementation details.
"""

import unittest
from unittest.mock import patch, MagicMock
import tempfile
import shutil
from pathlib import Path
from typer.testing import CliRunner

# Import the worklog module
from worklog import TaskEntry, PausedTask, WorkLogData, WorkLog, app


class TestDataClasses(unittest.TestCase):
    """Test the dataclass structures used in the worklog system."""
    
    def test_task_entry_creation(self):
        """Test TaskEntry dataclass creation."""
        from datetime import datetime
        start_time = datetime.now()
        
        entry = TaskEntry(
            task="Test Task",
            start_time=start_time,
            end_time=None
        )
        
        self.assertEqual(entry.task, "Test Task")
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
    
    def test_worklog_data_defaults(self):
        """Test WorkLogData default initialization."""
        data = WorkLogData()
        
        self.assertEqual(data.entries, [])
        self.assertEqual(data.active_tasks, {})
        self.assertEqual(data.paused_tasks, [])


class TestWorkLogBasicOperations(unittest.TestCase):
    """Test basic WorkLog operations without complex mocking."""
    
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
        """Test WorkLog initialization."""
        mock_home.return_value = self.test_home
        
        worklog = WorkLog()
        
        # Check that it creates the directory and loads data
        worklog_dir = self.test_home / '.worklog'
        self.assertTrue(worklog_dir.exists())
        self.assertIsNotNone(worklog.data)
    
    @patch('worklog.Path.home')
    def test_directory_creation(self, mock_home):
        """Test directory creation during initialization."""
        mock_home.return_value = self.test_home
        
        # Ensure directory doesn't exist initially
        worklog_dir = self.test_home / '.worklog'
        self.assertFalse(worklog_dir.exists())
        
        # Initialize WorkLog
        worklog = WorkLog()
        
        # Check directory was created
        self.assertTrue(worklog_dir.exists())
        self.assertEqual(worklog.worklog_dir, worklog_dir)


class TestStaticMethods(unittest.TestCase):
    """Test static utility methods."""
    
    def test_get_current_timestamp(self):
        """Test current timestamp generation."""
        result = WorkLog._get_current_timestamp()
        
        # Should be a string in ISO format
        self.assertIsInstance(result, str)
        self.assertIn("T", result)  # ISO format contains T
        self.assertTrue(len(result) >= 19)  # At least YYYY-MM-DDTHH:MM:SS
    
    def test_parse_custom_time_valid(self):
        """Test parsing valid custom time."""
        result = WorkLog._parse_custom_time("14:30")
        
        # Should return ISO timestamp string for today at 14:30
        self.assertIsInstance(result, str)
        self.assertIn("T14:30:00", result)
    
    def test_parse_custom_time_invalid(self):
        """Test parsing invalid custom time raises ValueError."""
        with self.assertRaises(ValueError):
            WorkLog._parse_custom_time("25:00")  # Invalid hour
        
        with self.assertRaises(ValueError):
            WorkLog._parse_custom_time("12:60")  # Invalid minute
        
        with self.assertRaises(ValueError):
            WorkLog._parse_custom_time("abc")    # Invalid format
    
    def test_format_duration(self):
        """Test duration formatting."""
        start = "2025-10-03T09:00:00"
        end = "2025-10-03T10:30:45"
        
        result = WorkLog._format_duration(start, end)
        self.assertEqual(result, "01:30:45")
    
    def test_format_display_time(self):
        """Test timestamp formatting for display."""
        timestamp = "2025-10-03T14:30:15"
        
        result = WorkLog._format_display_time(timestamp)
        self.assertEqual(result, "2025-10-03 14:30:15")


class TestTaskOperations(unittest.TestCase):
    """Test task operations with minimal mocking."""
    
    def setUp(self):
        """Set up WorkLog instance for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_home = Path(self.temp_dir) / "test_home"
        self.test_home.mkdir()
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    @patch('worklog.Path.home')
    def test_handle_task_new_task(self, mock_home):
        """Test handling a new task (start behavior)."""
        mock_home.return_value = self.test_home
        
        worklog = WorkLog()
        
        # Should start new task
        result = worklog.handle_task("Test Task")
        self.assertTrue(result)
        
        # Verify task is now active
        self.assertIn("Test Task", worklog.data.active_tasks)
    
    @patch('worklog.Path.home')
    def test_handle_task_toggle_existing(self, mock_home):
        """Test handling an existing active task (stop behavior)."""
        mock_home.return_value = self.test_home
        
        worklog = WorkLog()
        
        # Start a task first
        worklog.handle_task("Test Task")
        self.assertIn("Test Task", worklog.data.active_tasks)
        
        # Handle same task again should stop it
        result = worklog.handle_task("Test Task")
        self.assertTrue(result)
        
        # Verify task is no longer active
        self.assertNotIn("Test Task", worklog.data.active_tasks)
    
    @patch('worklog.Path.home')
    def test_start_anonymous_session(self, mock_home):
        """Test starting anonymous work session."""
        mock_home.return_value = self.test_home
        
        worklog = WorkLog()
        
        result = worklog.start_anonymous_task()
        self.assertTrue(result)
        
        # Check anonymous task is active
        self.assertIn(worklog.ANONYMOUS_TASK_NAME, worklog.data.active_tasks)
    
    @patch('worklog.Path.home')
    def test_pause_and_resume_functionality(self, mock_home):
        """Test pause and resume operations."""
        mock_home.return_value = self.test_home
        
        worklog = WorkLog()
        
        # Start a task
        worklog.handle_task("Test Task")
        self.assertIn("Test Task", worklog.data.active_tasks)
        
        # Pause all tasks
        worklog.pause_all_tasks()
        self.assertEqual(len(worklog.data.active_tasks), 0)
        self.assertEqual(len(worklog.data.paused_tasks), 1)
        
        # Resume last task
        result = worklog.resume_last_task()
        self.assertTrue(result)
        self.assertEqual(len(worklog.data.paused_tasks), 0)
        self.assertIn("Test Task", worklog.data.active_tasks)
    
    @patch('worklog.Path.home')
    def test_stop_all_tasks(self, mock_home):
        """Test stopping all active tasks."""
        mock_home.return_value = self.test_home
        
        worklog = WorkLog()
        
        # Start multiple tasks
        worklog.handle_task("Task 1", parallel_mode=True)
        worklog.handle_task("Task 2", parallel_mode=True)
        self.assertEqual(len(worklog.data.active_tasks), 2)
        
        # Stop all tasks
        worklog.stop_all_tasks()
        self.assertEqual(len(worklog.data.active_tasks), 0)


class TestCLICommands(unittest.TestCase):
    """Test CLI commands using Typer's test runner."""
    
    def setUp(self):
        """Set up CLI test runner."""
        self.runner = CliRunner()
    
    def test_help_command(self):
        """Test main help command."""
        result = self.runner.invoke(app, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Track work time on tasks", result.stdout)
    
    def test_task_command_help(self):
        """Test task command help includes short options."""
        result = self.runner.invoke(app, ["task", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("-p", result.stdout)  # Parallel short option
        self.assertIn("-t", result.stdout)  # Time short option
    
    def test_recent_command_help(self):
        """Test recent command help includes count option."""
        result = self.runner.invoke(app, ["recent", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("-c", result.stdout)  # Count short option
    
    def test_start_command_help(self):
        """Test start command help includes time option."""
        result = self.runner.invoke(app, ["start", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("-t", result.stdout)  # Time short option
    
    def test_all_commands_exist(self):
        """Test that all expected commands exist."""
        result = self.runner.invoke(app, ["--help"])
        self.assertEqual(result.exit_code, 0)
        
        expected_commands = [
            "task", "start", "stop", "pause", "resume", 
            "clean", "list", "recent", "today", "date"
        ]
        
        for command in expected_commands:
            with self.subTest(command=command):
                self.assertIn(command, result.stdout)
    
    def test_clean_command_help(self):
        """Test clean command help includes date option."""
        result = self.runner.invoke(app, ["clean", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("-d", result.stdout)  # Date short option
        self.assertIn("--date", result.stdout)  # Date long option
        self.assertIn("YYYY-MM-DD", result.stdout)  # Date format info
    
    def test_clean_command_invalid_date_format(self):
        """Test clean command with invalid date format."""
        result = self.runner.invoke(app, ["clean", "--date", "invalid-date"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Invalid date format", result.stdout)
    
    def test_clean_command_short_date_format(self):
        """Test clean command with short date format (should fail)."""
        result = self.runner.invoke(app, ["clean", "-d", "10-03"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Invalid date format", result.stdout)


class TestCleanFunctionality(unittest.TestCase):
    """Test clean command functionality with date options."""
    
    def setUp(self):
        """Set up temporary directory and test data."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_home = Path(self.temp_dir) / "test_home"
        self.test_home.mkdir()
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    @patch('worklog.Path.home')
    @patch('typer.confirm')
    def test_clean_specific_date_no_entries(self, mock_confirm, mock_home):
        """Test cleaning a date with no entries."""
        mock_home.return_value = self.test_home
        mock_confirm.return_value = True
        
        worklog = WorkLog()
        
        # Should handle empty date gracefully
        worklog.clean_date_worklog("2025-09-30")
        
        # Should not have called confirm since no entries exist
        mock_confirm.assert_not_called()
    
    @patch('worklog.Path.home') 
    @patch('typer.confirm')
    def test_clean_specific_date_with_entries(self, mock_confirm, mock_home):
        """Test cleaning a date with entries."""
        mock_home.return_value = self.test_home
        mock_confirm.return_value = True
        
        worklog = WorkLog()
        
        # Add test entries for specific date
        test_entry = TaskEntry(
            task="Test Task",
            start_time="2025-10-01T09:00:00",
            end_time="2025-10-01T10:00:00",
            duration="01:00:00"
        )
        worklog.data.entries.append(test_entry)
        
        # Clean the specific date
        worklog.clean_date_worklog("2025-10-01")
        
        # Should have asked for confirmation
        mock_confirm.assert_called_once()
        
        # Entry should be removed
        remaining_entries = [e for e in worklog.data.entries if e.start_time.startswith("2025-10-01")]
        self.assertEqual(len(remaining_entries), 0)
    
    @patch('worklog.Path.home')
    @patch('typer.confirm') 
    def test_clean_specific_date_cancelled(self, mock_confirm, mock_home):
        """Test cleaning cancelled by user."""
        mock_home.return_value = self.test_home
        mock_confirm.return_value = False  # User cancels
        
        worklog = WorkLog()
        
        # Add test entry
        test_entry = TaskEntry(
            task="Test Task",
            start_time="2025-10-01T09:00:00",
            end_time="2025-10-01T10:00:00", 
            duration="01:00:00"
        )
        worklog.data.entries.append(test_entry)
        original_count = len(worklog.data.entries)
        
        # Clean should be cancelled
        worklog.clean_date_worklog("2025-10-01")
        
        # Entry should still exist
        self.assertEqual(len(worklog.data.entries), original_count)
    
    @patch('worklog.Path.home')
    def test_clean_today_uses_date_method(self, mock_home):
        """Test that clean_today_worklog uses clean_date_worklog internally."""
        mock_home.return_value = self.test_home
        
        worklog = WorkLog()
        
        # Mock the clean_date_worklog method to verify it's called
        with patch.object(worklog, 'clean_date_worklog') as mock_clean_date:
            worklog.clean_today_worklog()
            
            # Should have called clean_date_worklog with today's date
            mock_clean_date.assert_called_once()
            # Verify it was called with today's date format
            called_args = mock_clean_date.call_args[0]
            self.assertEqual(len(called_args), 1)
            self.assertRegex(called_args[0], r'^\d{4}-\d{2}-\d{2}$')  # YYYY-MM-DD format


class TestDataPersistence(unittest.TestCase):
    """Test data loading and saving functionality."""
    
    def setUp(self):
        """Set up temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_home = Path(self.temp_dir) / "test_home"
        self.test_home.mkdir()
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    @patch('worklog.Path.home')
    def test_data_persistence(self, mock_home):
        """Test that data persists across WorkLog instances."""
        mock_home.return_value = self.test_home
        
        # Create first instance and add data
        worklog1 = WorkLog()
        worklog1.handle_task("Persistent Task")
        
        # Create second instance and verify data persists
        worklog2 = WorkLog()
        self.assertIn("Persistent Task", worklog2.data.active_tasks)
    
    @patch('worklog.Path.home')
    def test_empty_data_initialization(self, mock_home):
        """Test initialization with no existing data."""
        mock_home.return_value = self.test_home
        
        worklog = WorkLog()
        
        # Should have empty data structures
        self.assertEqual(len(worklog.data.entries), 0)
        self.assertEqual(len(worklog.data.active_tasks), 0)
        self.assertEqual(len(worklog.data.paused_tasks), 0)


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for common usage scenarios."""
    
    def setUp(self):
        """Set up temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_home = Path(self.temp_dir) / "test_home"
        self.test_home.mkdir()
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    @patch('worklog.Path.home')
    def test_typical_workflow(self, mock_home):
        """Test a typical work session workflow."""
        mock_home.return_value = self.test_home
        
        worklog = WorkLog()
        
        # Start a task
        result = worklog.handle_task("Morning Tasks")
        self.assertTrue(result)
        self.assertIn("Morning Tasks", worklog.data.active_tasks)
        
        # Pause for lunch
        worklog.pause_all_tasks()
        self.assertEqual(len(worklog.data.active_tasks), 0)
        self.assertEqual(len(worklog.data.paused_tasks), 1)
        
        # Resume after lunch
        result = worklog.resume_last_task()
        self.assertTrue(result)
        self.assertIn("Morning Tasks", worklog.data.active_tasks)
        
        # Switch to different task
        result = worklog.handle_task("Afternoon Meeting")
        self.assertTrue(result)
        self.assertIn("Afternoon Meeting", worklog.data.active_tasks)
        self.assertNotIn("Morning Tasks", worklog.data.active_tasks)  # Single-task mode
        
        # End day - stop all tasks
        worklog.stop_all_tasks()
        self.assertEqual(len(worklog.data.active_tasks), 0)
        self.assertEqual(len(worklog.data.paused_tasks), 0)
    
    @patch('worklog.Path.home')
    def test_parallel_mode_workflow(self, mock_home):
        """Test working with multiple concurrent tasks."""
        mock_home.return_value = self.test_home
        
        worklog = WorkLog()
        
        # Start first task
        worklog.handle_task("Development", parallel_mode=True)
        self.assertIn("Development", worklog.data.active_tasks)
        
        # Start second task in parallel
        worklog.handle_task("Code Review", parallel_mode=True)
        self.assertEqual(len(worklog.data.active_tasks), 2)
        
        # Stop one specific task
        worklog.handle_task("Development")  # Toggle off
        self.assertEqual(len(worklog.data.active_tasks), 1)
        self.assertIn("Code Review", worklog.data.active_tasks)
        self.assertNotIn("Development", worklog.data.active_tasks)


if __name__ == '__main__':
    # Run all tests with verbose output
    unittest.main(verbosity=2)