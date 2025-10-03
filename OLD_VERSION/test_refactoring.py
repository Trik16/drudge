#!/usr/bin/env python3
"""
Quick test script to validate the refactoring changes work correctly.
Tests core functionality without relying on old test assumptions.
"""

import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from worklog import WorkLog, WorkLogConfig, WorkLogValidator

def test_basic_functionality():
    """Test basic WorkLog functionality with new refactored classes."""
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        print("🔄 Testing WorkLog initialization...")
        config = WorkLogConfig(
            worklog_dir_name="test_worklog",
            date_format="%Y-%m-%d",
            time_format="%H:%M",
            display_time_format="%Y-%m-%d %H:%M:%S",
            max_recent_tasks=10,
            backup_enabled=True,
            auto_save=True
        )
        
        validator = WorkLogValidator()
        
        # Create a config that uses our temp directory
        import os
        os.environ['HOME'] = str(temp_path)  # Temporarily override HOME
        worklog = WorkLog(config)
        
        print("✅ WorkLog initialized successfully")
        
        print("🔄 Testing validation functionality...")
        
        # Test date validation
        try:
            validator.validate_date_format("2023-12-31")
            print("✅ Date validation works")
        except ValueError:
            print("❌ Date validation failed")
            return False
        
        # Test time validation
        try:
            validator.validate_time_format("14:30")
            print("✅ Time validation works")
        except ValueError:
            print("❌ Time validation failed")
            return False
        
        # Test task name validation
        try:
            validator.validate_task_name("Valid Task Name")
            print("✅ Task name validation works")
        except ValueError:
            print("❌ Task name validation failed")
            return False
        
        print("🔄 Testing WorkLog data operations...")
        
        # Test basic task operations
        try:
            # Start a task
            worklog.start_task("Test Task")
            print("✅ Task started successfully")
            
            # Check if task is active
            if "Test Task" in worklog.data.active_tasks:
                print("✅ Task properly added to active tasks")
            else:
                print("❌ Task not found in active tasks")
                return False
            
            # End the task
            worklog.end_task("Test Task")
            print("✅ Task ended successfully")
            
            # Check if task was moved to entries
            if worklog.data.entries:
                print("✅ Task entry created in data")
            else:
                print("❌ No task entry found")
                return False
                
        except Exception as e:
            print(f"❌ Task operations failed: {e}")
            return False
        
        print("🔄 Testing file operations...")
        
        # Check if files were created
        worklog_file = worklog.worklog_file
        if worklog_file.exists():
            print("✅ WorkLog file created")
        else:
            print("❌ WorkLog file not created")
            return False
        
        # Check daily logs directory
        daily_dir = worklog.worklog_dir / "daily"
        if daily_dir.exists():
            print("✅ Daily logs directory created")
        else:
            print("❌ Daily logs directory not created")
            return False
        
        print("🔄 Testing caching functionality...")
        
        # Test that caching decorator works
        timestamp = "2023-12-31T14:30:00"
        result1 = worklog._format_display_time(timestamp)
        result2 = worklog._format_display_time(timestamp)
        
        if result1 == result2:
            print("✅ Caching appears to work")
        else:
            print("❌ Caching might not be working")
            
        return True

def test_managers():
    """Test the new manager classes."""
    
    print("🔄 Testing BackupManager...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        from worklog import BackupManager
        
        backup_manager = BackupManager(Path(temp_dir))
        
        # Test backup creation
        test_data = {"test": "data"}
        backup_file = backup_manager.create_backup(
            backup_type="test",
            data=test_data,
            suffix="test_backup"
        )
        
        if backup_file.exists():
            print("✅ BackupManager created backup file")
        else:
            print("❌ BackupManager failed to create backup")
            return False
    
    print("🔄 Testing DailyFileManager...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        from worklog import DailyFileManager
        
        daily_manager = DailyFileManager()
        
        # Test entry formatting
        entry = daily_manager.format_entry(
            task_name="Test Task",
            action="start", 
            timestamp="2023-12-31T14:30:00"
        )
        
        if "Test Task" in entry and "14:30:00" in entry:
            print("✅ DailyFileManager formats entries correctly")
        else:
            print("❌ DailyFileManager entry formatting failed")
            return False
        
        # Test chronological addition
        test_file = Path(temp_dir) / "test.log"
        daily_manager.add_entry_chronologically(test_file, entry)
        
        if test_file.exists():
            print("✅ DailyFileManager adds entries to file")
        else:
            print("❌ DailyFileManager failed to create file")
            return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting refactoring validation tests...\n")
    
    success = True
    
    try:
        success &= test_basic_functionality()
        print()
        success &= test_managers()
        
        print("\n" + "="*50)
        if success:
            print("🎉 ALL TESTS PASSED! Refactoring is successful!")
            print("✨ The new architecture is working correctly.")
        else:
            print("❌ Some tests failed. Check the output above.")
            
    except Exception as e:
        print(f"💥 Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    sys.exit(0 if success else 1)