#!/usr/bin/env python3
"""
Simple validation script to verify core WorkLog functionality after refactoring.
"""

import tempfile
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from worklog import WorkLog

def main():
    """Test basic WorkLog operations to verify refactoring didn't break functionality."""
    
    print("🔄 Testing basic WorkLog functionality...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Override HOME to use temp directory
        original_home = os.environ.get('HOME')
        os.environ['HOME'] = temp_dir
        
        try:
            # Initialize WorkLog
            worklog = WorkLog()
            print("✅ WorkLog initialized successfully")
            
            # Start a task
            worklog.start_task("Test Refactoring Task")
            print("✅ Task started successfully")
            
            # Check if task is active
            if "Test Refactoring Task" in worklog.data.active_tasks:
                print("✅ Task found in active tasks")
            else:
                print("❌ Task not found in active tasks")
                return False
            
            # End the task
            worklog.end_task("Test Refactoring Task")
            print("✅ Task ended successfully")
            
            # Check if entry was created
            if worklog.data.entries:
                print("✅ Task entry created successfully")
                print(f"   📊 Total entries: {len(worklog.data.entries)}")
            else:
                print("❌ No task entries found")
                return False
            
            # Test pause/resume functionality  
            worklog.start_task("Pause Test Task")
            worklog.pause_all_tasks()
            
            if worklog.data.paused_tasks:
                print("✅ Pause functionality works")
                print(f"   📊 Paused tasks: {[task.task for task in worklog.data.paused_tasks]}")
            else:
                print("❌ Pause functionality failed")
                return False
            
            worklog.resume_last_task()
            
            if "Pause Test Task" in worklog.data.active_tasks:
                print("✅ Resume functionality works")  
            else:
                print("❌ Resume functionality failed")
                return False
            
            worklog.end_task("Pause Test Task")
            
            print("\n🎉 All basic functionality tests passed!")
            print("✨ Refactoring appears successful - core features working!")
            return True
            
        except Exception as e:
            print(f"❌ Error during testing: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            # Restore original HOME
            if original_home:
                os.environ['HOME'] = original_home
            elif 'HOME' in os.environ:
                del os.environ['HOME']

if __name__ == "__main__":
    success = main()
    print(f"\n{'='*60}")
    if success:
        print("🌟 VALIDATION SUCCESSFUL - Refactoring works correctly! 🌟")
    else:
        print("💥 VALIDATION FAILED - Issues need to be addressed")
    sys.exit(0 if success else 1)