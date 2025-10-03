#!/usr/bin/env python3
"""
WorkLog CLI Tool

A simple CLI tool to track work time on tasks.
Usage: worklog [TASKNAME]

First run: Starts tracking time for a task
Second run: Ends the task and calculates duration

The tool maintains a JSON file to store task history and current active tasks.
"""

import json
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import os

class WorkLog:
    ANONYMOUS_TASK_NAME = "__ANONYMOUS_WORK__"
    
    def __init__(self):
        # Store worklog files in user's home directory
        self.worklog_dir = Path.home() / '.worklog'
        self.worklog_file = self.worklog_dir / 'worklog.json'
        
        # Create directory if it doesn't exist
        self._ensure_directory()
        
        # Migrate old file if exists
        self._migrate_old_file()
        
        self.data = self._load_data()
    
    def _ensure_directory(self):
        """Create .worklog directory if it doesn't exist"""
        self.worklog_dir.mkdir(exist_ok=True)
    
    def _migrate_old_file(self):
        """Migrate old .worklog.json from home directory to .worklog/worklog.json"""
        old_file = Path.home() / '.worklog.json'
        if old_file.exists() and not self.worklog_file.exists():
            try:
                # Copy old file to new location
                with open(old_file, 'r') as f:
                    data = f.read()
                with open(self.worklog_file, 'w') as f:
                    f.write(data)
                
                # Remove old file after successful migration
                old_file.unlink()
                print(f"Migrated worklog data to {self.worklog_dir}")
            except (IOError, OSError) as e:
                print(f"Warning: Could not migrate old worklog file: {e}")
    
    def _get_daily_file_path(self, date_str=None):
        """Get path for daily readable file (YYYY-MM-DD.txt)"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        return self.worklog_dir / f"{date_str}.txt"
    
    def _update_daily_file(self, task_name, action, timestamp, duration=None):
        """Update the daily readable text file with task information"""
        dt = datetime.fromisoformat(timestamp)
        date_str = dt.strftime("%Y-%m-%d")
        time_str = dt.strftime("%H:%M:%S")
        
        daily_file = self._get_daily_file_path(date_str)
        
        # Read existing content
        existing_lines = []
        if daily_file.exists():
            try:
                with open(daily_file, 'r', encoding='utf-8') as f:
                    existing_lines = f.readlines()
            except IOError:
                pass
        
        # Prepare new content
        if action == 'start':
            # Format: DATE TIME TASK_NAME [ACTIVE]
            if task_name == self.ANONYMOUS_TASK_NAME:
                display_name = "[ANONYMOUS WORK]"
            else:
                display_name = task_name
            new_line = f"{date_str} {time_str} {display_name} [ACTIVE]\n"
            existing_lines.append(new_line)
        elif action == 'end':
            # Find the corresponding ACTIVE entry and update it with duration
            for i in range(len(existing_lines) - 1, -1, -1):
                line = existing_lines[i].strip()
                if line.endswith(f"{task_name} [ACTIVE]"):
                    # Extract date and time from the beginning of the line
                    parts = line.split(' ')
                    if len(parts) >= 3:
                        start_date = parts[0]
                        start_time = parts[1]
                        # Format: START_DATE START_TIME TASK_NAME (WORKED_TIME)
                        existing_lines[i] = f"{start_date} {start_time} {task_name} ({duration})\n"
                    break
            else:
                # If no ACTIVE entry found, add completed entry anyway
                new_line = f"{date_str} {time_str} {task_name} ({duration})\n"
                existing_lines.append(new_line)
        
        # Write updated content
        try:
            with open(daily_file, 'w', encoding='utf-8') as f:
                f.writelines(existing_lines)
        except IOError as e:
            print(f"Warning: Could not update daily file: {e}")
    
    def _update_anonymous_daily_file(self, new_task_name, start_time):
        """Update daily file to replace anonymous task with named task"""
        dt = datetime.fromisoformat(start_time)
        date_str = dt.strftime("%Y-%m-%d")
        
        daily_file = self._get_daily_file_path(date_str)
        
        if not daily_file.exists():
            return
        
        try:
            # Read existing content
            with open(daily_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Find and replace the anonymous task line
            for i, line in enumerate(lines):
                if "[ANONYMOUS WORK]" in line:
                    # Extract date and time from the line
                    parts = line.strip().split(' ')
                    if len(parts) >= 3:
                        date_part = parts[0]
                        time_part = parts[1]
                        # Replace with named task
                        lines[i] = f"{date_part} {time_part} {new_task_name} [ACTIVE]\n"
                        break
            
            # Write back the updated content
            with open(daily_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
                
        except IOError as e:
            print(f"Warning: Could not update daily file: {e}")
    
    def _load_data(self):
        """Load existing worklog data or create new structure"""
        if not self.worklog_file.exists():
            return {
                'entries': [],
                'active_tasks': {},
                'paused_tasks': []
            }
        
        try:
            with open(self.worklog_file, 'r') as f:
                data = json.load(f)
                # Ensure backward compatibility - add paused_tasks if missing
                if 'paused_tasks' not in data:
                    data['paused_tasks'] = []
                return data
        except (json.JSONDecodeError, IOError):
            # If file is corrupted, start fresh but backup the old one
            if self.worklog_file.exists():
                backup_file = self.worklog_file.with_suffix('.json.backup')
                self.worklog_file.rename(backup_file)
                print(f"Warning: Corrupted worklog file backed up to {backup_file}")
            
            return {
                'entries': [],
                'active_tasks': {},
                'paused_tasks': []
            }
    
    def _save_data(self):
        """Save worklog data to file"""
        try:
            with open(self.worklog_file, 'w') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving worklog: {e}")
            sys.exit(1)
    
    def _get_current_timestamp(self):
        """Get current timestamp in ISO format"""
        return datetime.now().isoformat()
    
    def _parse_custom_time(self, time_str):
        """Parse HH:MM time string and create timestamp for today"""
        try:
            # Parse the time string
            time_parts = time_str.split(':')
            if len(time_parts) != 2:
                raise ValueError("Invalid time format")
            
            hours = int(time_parts[0])
            minutes = int(time_parts[1])
            
            # Validate ranges
            if not (0 <= hours <= 23):
                raise ValueError("Hours must be between 00-23")
            if not (0 <= minutes <= 59):
                raise ValueError("Minutes must be between 00-59")
            
            # Create datetime for today with specified time
            today = datetime.now().date()
            custom_datetime = datetime.combine(today, datetime.min.time().replace(hour=hours, minute=minutes))
            
            return custom_datetime.isoformat()
            
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid time format '{time_str}'. Use HH:MM format (e.g., 09:30)")
    
    def _get_timestamp(self, custom_time=None):
        """Get timestamp - current time or custom time for today"""
        if custom_time:
            return self._parse_custom_time(custom_time)
        return self._get_current_timestamp()
    
    def _format_duration(self, start_time, end_time):
        """Calculate and format duration between two timestamps"""
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time)
        
        duration = end_dt - start_dt
        
        # Format duration as HH:MM:SS
        hours, remainder = divmod(duration.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    
    def _format_display_time(self, timestamp):
        """Format timestamp for display (date and time)"""
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def _format_start_time_compact(self, timestamp):
        """Format timestamp for compact display (date and time only)"""
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def start_task(self, task_name, custom_start_time=None):
        """Start tracking a new task"""
        start_time = self._get_timestamp(custom_start_time)
        
        # Check if task is already active
        if task_name in self.data['active_tasks']:
            print(f"Task '{task_name}' is already active since {self._format_display_time(self.data['active_tasks'][task_name])}")
            return
        
        # Add to active tasks
        self.data['active_tasks'][task_name] = start_time
        
        # Create new entry
        entry = {
            'task': task_name,
            'start_time': start_time,
            'end_time': None,
            'duration': None
        }
        
        self.data['entries'].append(entry)
        self._save_data()
        
        # Update daily file
        self._update_daily_file(task_name, 'start', start_time)
        
        print(f"Started tracking task: '{task_name}' at {self._format_display_time(start_time)}")
    
    def start_anonymous_task(self):
        """Start an anonymous work session to be named later, or resume last paused task"""
        # First check if there are paused tasks to resume
        if self.data['paused_tasks']:
            return self.resume_last_task()
        
        current_time = self._get_current_timestamp()
        
        # Check if there's already an anonymous task active
        if self.ANONYMOUS_TASK_NAME in self.data['active_tasks']:
            existing_time = self.data['active_tasks'][self.ANONYMOUS_TASK_NAME]
            print(f"Anonymous work session already active since {self._format_display_time(existing_time)}")
            return
        
        # Add to active tasks
        self.data['active_tasks'][self.ANONYMOUS_TASK_NAME] = current_time
        
        # Create new entry
        entry = {
            'task': self.ANONYMOUS_TASK_NAME,
            'start_time': current_time,
            'end_time': None,
            'duration': None
        }
        
        self.data['entries'].append(entry)
        self._save_data()
        
        # Update daily file with anonymous task
        self._update_daily_file(self.ANONYMOUS_TASK_NAME, 'start', current_time)
        
        print(f"Started anonymous work session at {self._format_display_time(current_time)}")
        print("Use 'worklog \"Task Name\"' to assign a name to this session.")
    
    def start_anonymous_task_at_time(self, custom_time):
        """Start an anonymous work session at a custom time"""
        # Check if there's already an anonymous task active
        if self.ANONYMOUS_TASK_NAME in self.data['active_tasks']:
            existing_time = self.data['active_tasks'][self.ANONYMOUS_TASK_NAME]
            print(f"Anonymous work session already active since {self._format_display_time(existing_time)}")
            return
        
        # Parse and use custom time
        start_time = self._parse_custom_time(custom_time)
        
        # Add to active tasks
        self.data['active_tasks'][self.ANONYMOUS_TASK_NAME] = start_time
        
        # Create new entry
        entry = {
            'task': self.ANONYMOUS_TASK_NAME,
            'start_time': start_time,
            'end_time': None,
            'duration': None
        }
        
        self.data['entries'].append(entry)
        self._save_data()
        
        # Update daily file with anonymous task
        self._update_daily_file(self.ANONYMOUS_TASK_NAME, 'start', start_time)
        
        print(f"Started anonymous work session at {self._format_display_time(start_time)}")
        print("Use 'worklog \"Task Name\"' to assign a name to this session.")
    
    def end_task(self, task_name):
        """End tracking a task and calculate duration"""
        current_time = self._get_current_timestamp()
        
        # Check if task is active
        if task_name not in self.data['active_tasks']:
            print(f"Task '{task_name}' is not currently active.")
            return
        
        start_time = self.data['active_tasks'][task_name]
        
        # Find the corresponding entry and update it
        for entry in reversed(self.data['entries']):
            if (entry['task'] == task_name and 
                entry['start_time'] == start_time and 
                entry['end_time'] is None):
                
                entry['end_time'] = current_time
                entry['duration'] = self._format_duration(start_time, current_time)
                break
        
        # Remove from active tasks
        del self.data['active_tasks'][task_name]
        
        self._save_data()
        
        duration = self._format_duration(start_time, current_time)
        
        # Update daily file
        self._update_daily_file(task_name, 'end', current_time, duration)
        
        print(f"Finished task: '{task_name}' at {self._format_display_time(current_time)}")
        print(f"Duration: {duration}")
    
    def handle_task(self, task_name, parallel_mode=False, custom_start_time=None):
        """Main handler - decides whether to start or end a task"""
        # Check if there's an anonymous task to convert
        if (self.ANONYMOUS_TASK_NAME in self.data['active_tasks'] and 
            task_name != self.ANONYMOUS_TASK_NAME and 
            task_name not in self.data['active_tasks']):
            self._convert_anonymous_task(task_name)
        elif task_name in self.data['active_tasks']:
            if custom_start_time:
                print("Warning: --start-time ignored when ending a task")
            self.end_task(task_name)
        else:
            # Single-task mode: stop all other active tasks unless parallel mode
            if not parallel_mode and self.data['active_tasks']:
                self._stop_other_tasks(exclude_task=task_name)
            self.start_task(task_name, custom_start_time)
    
    def _convert_anonymous_task(self, new_task_name):
        """Convert an active anonymous task to a named task"""
        if self.ANONYMOUS_TASK_NAME not in self.data['active_tasks']:
            return False
        
        anonymous_start_time = self.data['active_tasks'][self.ANONYMOUS_TASK_NAME]
        
        # Update active tasks
        del self.data['active_tasks'][self.ANONYMOUS_TASK_NAME]
        self.data['active_tasks'][new_task_name] = anonymous_start_time
        
        # Find and update the corresponding entry
        for entry in reversed(self.data['entries']):
            if (entry['task'] == self.ANONYMOUS_TASK_NAME and 
                entry['start_time'] == anonymous_start_time and 
                entry['end_time'] is None):
                entry['task'] = new_task_name
                break
        
        self._save_data()
        
        # Update daily file - replace anonymous entry with named one
        self._update_anonymous_daily_file(new_task_name, anonymous_start_time)
        
        print(f"Converted anonymous session to: '{new_task_name}' (started at {self._format_display_time(anonymous_start_time)})")
        return True
    
    def _stop_other_tasks(self, exclude_task=None):
        """Stop all active tasks except the excluded one (for single-task mode)"""
        if not self.data['active_tasks']:
            return
        
        current_time = self._get_current_timestamp()
        stopped_tasks = []
        
        for task_name in list(self.data['active_tasks'].keys()):
            if exclude_task and task_name == exclude_task:
                continue
                
            start_time = self.data['active_tasks'][task_name]
            
            # Find and update the corresponding entry
            for entry in reversed(self.data['entries']):
                if (entry['task'] == task_name and 
                    entry['start_time'] == start_time and 
                    entry['end_time'] is None):
                    
                    entry['end_time'] = current_time
                    entry['duration'] = self._format_duration(start_time, current_time)
                    break
            
            # Update daily file
            duration = self._format_duration(start_time, current_time)
            self._update_daily_file(task_name, 'end', current_time, duration)
            
            stopped_tasks.append((task_name, duration))
            del self.data['active_tasks'][task_name]
        
        if stopped_tasks:
            print("Stopped previous task(s) (single-task mode):")
            for task_name, duration in stopped_tasks:
                display_name = "[ANONYMOUS WORK]" if task_name == self.ANONYMOUS_TASK_NAME else task_name
                print(f"  - {display_name} ({duration})")
        
        self._save_data()
    
    def stop_all_tasks(self):
        """Stop all currently active tasks and clear paused tasks"""
        active_count = len(self.data['active_tasks'])
        paused_count = len(self.data['paused_tasks'])
        
        if active_count == 0 and paused_count == 0:
            print("No active or paused tasks to stop.")
            return
        
        current_time = self._get_current_timestamp()
        stopped_tasks = []
        
        # Stop active tasks
        for task_name in list(self.data['active_tasks'].keys()):
            start_time = self.data['active_tasks'][task_name]
            
            # Find and update the corresponding entry
            for entry in reversed(self.data['entries']):
                if (entry['task'] == task_name and 
                    entry['start_time'] == start_time and 
                    entry['end_time'] is None):
                    
                    entry['end_time'] = current_time
                    entry['duration'] = self._format_duration(start_time, current_time)
                    break
            
            # Update daily file
            duration = self._format_duration(start_time, current_time)
            self._update_daily_file(task_name, 'end', current_time, duration)
            
            stopped_tasks.append((task_name, duration, "active"))
        
        # Clear paused tasks (they're already completed in entries)
        cleared_paused = []
        for paused_task in self.data['paused_tasks']:
            task_name = paused_task['task']
            total_time = paused_task['total_duration_so_far']
            cleared_paused.append((task_name, total_time, "paused"))
        
        # Clear all tasks
        self.data['active_tasks'].clear()
        self.data['paused_tasks'].clear()
        self._save_data()
        
        if stopped_tasks:
            print(f"Stopped {len(stopped_tasks)} active task(s):")
            for task_name, duration, _ in stopped_tasks:
                display_name = "[ANONYMOUS WORK]" if task_name == self.ANONYMOUS_TASK_NAME else task_name
                print(f"  - {display_name} ({duration})")
        
        if cleared_paused:
            print(f"Cleared {len(cleared_paused)} paused task(s):")
            for task_name, total_time, _ in cleared_paused:
                display_name = "[ANONYMOUS WORK]" if task_name == self.ANONYMOUS_TASK_NAME else task_name
                print(f"  - {display_name} (total time: {total_time})")
    
    def pause_all_tasks(self):
        """Pause all currently active tasks"""
        if not self.data['active_tasks']:
            print("No active tasks to pause.")
            return
        
        current_time = self._get_current_timestamp()
        paused_tasks = []
        
        for task_name in list(self.data['active_tasks'].keys()):
            start_time = self.data['active_tasks'][task_name]
            
            # Find and update the corresponding entry
            for entry in reversed(self.data['entries']):
                if (entry['task'] == task_name and 
                    entry['start_time'] == start_time and 
                    entry['end_time'] is None):
                    
                    entry['end_time'] = current_time
                    entry['duration'] = self._format_duration(start_time, current_time)
                    break
            
            # Update daily file
            duration = self._format_duration(start_time, current_time)
            self._update_daily_file(task_name, 'end', current_time, duration)
            
            # Add to paused tasks list
            paused_task = {
                'task': task_name,
                'paused_at': current_time,
                'total_duration_so_far': self._calculate_total_duration(task_name)
            }
            self.data['paused_tasks'].append(paused_task)
            
            paused_tasks.append((task_name, duration))
        
        # Clear all active tasks
        self.data['active_tasks'].clear()
        self._save_data()
        
        print(f"Paused {len(paused_tasks)} task(s):")
        for task_name, duration in paused_tasks:
            display_name = "[ANONYMOUS WORK]" if task_name == self.ANONYMOUS_TASK_NAME else task_name
            print(f"  - {display_name} (session: {duration})")
        print("Use 'worklog --resume' or 'worklog --start' to resume the last paused task.")
    
    def _calculate_total_duration(self, task_name):
        """Calculate total duration spent on a task across all sessions"""
        total_seconds = 0
        
        for entry in self.data['entries']:
            if entry['task'] == task_name and entry['duration']:
                # Parse duration HH:MM:SS
                time_parts = entry['duration'].split(':')
                if len(time_parts) == 3:
                    hours, minutes, seconds = map(int, time_parts)
                    total_seconds += hours * 3600 + minutes * 60 + seconds
        
        # Format back to HH:MM:SS
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    
    def resume_last_task(self):
        """Resume the most recently paused task"""
        if not self.data['paused_tasks']:
            print("No paused tasks to resume.")
            return False
        
        # Get the most recent paused task
        last_paused = self.data['paused_tasks'][-1]
        task_name = last_paused['task']
        
        # Check if task is already active
        if task_name in self.data['active_tasks']:
            display_name = "[ANONYMOUS WORK]" if task_name == self.ANONYMOUS_TASK_NAME else task_name
            print(f"Task '{display_name}' is already active.")
            return False
        
        # Start new session for this task
        current_time = self._get_current_timestamp()
        
        # Add to active tasks
        self.data['active_tasks'][task_name] = current_time
        
        # Create new entry
        entry = {
            'task': task_name,
            'start_time': current_time,
            'end_time': None,
            'duration': None
        }
        
        self.data['entries'].append(entry)
        
        # Remove from paused tasks
        self.data['paused_tasks'].remove(last_paused)
        
        self._save_data()
        
        # Update daily file
        self._update_daily_file(task_name, 'start', current_time)
        
        display_name = "[ANONYMOUS WORK]" if task_name == self.ANONYMOUS_TASK_NAME else task_name
        total_time = last_paused['total_duration_so_far']
        print(f"Resumed task: '{display_name}' at {self._format_display_time(current_time)}")
        print(f"Previous total time: {total_time}")
        return True
    
    def clean_today_worklog(self):
        """Clean today's worklog entries with confirmation and backup"""
        today_str = datetime.now().strftime("%Y-%m-%d")
        daily_file = self.worklog_dir / f"{today_str}.txt"
        
        # Check if there's anything to clean
        today_entries = [entry for entry in self.data['entries'] 
                        if entry['start_time'].startswith(today_str)]
        
        if not today_entries and not daily_file.exists():
            print(f"No worklog entries found for {today_str}")
            return
        
        # Show what will be cleaned
        print(f"Found {len(today_entries)} entries for {today_str}")
        if daily_file.exists():
            print(f"Daily file: {daily_file}")
        
        # Ask for confirmation
        confirm = input("Are you sure you want to clean today's worklog? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("Clean operation cancelled")
            return
        
        # Create backup if there are entries to clean
        if today_entries or daily_file.exists():
            backup_file = self.worklog_dir / f"{today_str}_backup.txt"
            backup_content = []
            
            # Add JSON entries to backup
            if today_entries:
                backup_content.append("=== JSON Entries ===")
                for entry in today_entries:
                    task = entry['task']
                    start = self._format_display_time(entry['start_time'])
                    if entry['end_time']:
                        end = self._format_display_time(entry['end_time'])
                        duration = entry['duration']
                        backup_content.append(f"{start} - {end} {task} ({duration})")
                    else:
                        backup_content.append(f"{start} - ACTIVE {task}")
                backup_content.append("")
            
            # Add daily file content to backup
            if daily_file.exists():
                backup_content.append("=== Daily File Content ===")
                with open(daily_file, 'r') as f:
                    backup_content.extend(f.read().splitlines())
            
            # Write backup
            with open(backup_file, 'w') as f:
                f.write('\n'.join(backup_content))
            print(f"Backup created: {backup_file}")
        
        # Clean JSON entries
        if today_entries:
            self.data['entries'] = [entry for entry in self.data['entries'] 
                                  if not entry['start_time'].startswith(today_str)]
            
            # Clean active tasks for today
            active_to_remove = []
            for task, start_time in self.data['active_tasks'].items():
                if start_time.startswith(today_str):
                    active_to_remove.append(task)
            
            for task in active_to_remove:
                del self.data['active_tasks'][task]
            
            self._save_data()
            print(f"Cleaned {len(today_entries)} JSON entries")
        
        # Clean daily file
        if daily_file.exists():
            daily_file.unlink()
            print(f"Removed daily file: {daily_file}")
        
        print(f"Clean completed for {today_str}")
    
    def list_active_tasks(self):
        """List all currently active tasks, or show today's log if none"""
        if not self.data['active_tasks']:
            print("NO ACTIVE TASK")
            print()  # Empty line for separation
            self.show_today_file()
            return
        
        print("Active tasks:")
        for task, start_time in self.data['active_tasks'].items():
            display_name = "[ANONYMOUS WORK]" if task == self.ANONYMOUS_TASK_NAME else task
            print(f"  - {display_name} (started at {self._format_display_time(start_time)})")
    
    def show_recent_entries(self, count=10):
        """Show recent worklog entries"""
        if not self.data['entries']:
            print("No worklog entries found.")
            return
        
        print(f"Recent {count} entries:")
        recent_entries = self.data['entries'][-count:]
        
        for entry in recent_entries:
            start_display = self._format_start_time_compact(entry['start_time'])
            display_name = "[ANONYMOUS WORK]" if entry['task'] == self.ANONYMOUS_TASK_NAME else entry['task']
            
            if entry['end_time']:
                # Format: START_DATE START_TIME TASK_NAME (WORKED_TIME)
                print(f"  {start_display} {display_name} ({entry['duration']})")
            else:
                # For active tasks, show without duration
                print(f"  {start_display} {display_name} [ACTIVE]")
    
    def show_today_file(self):
        """Show today's readable daily file content"""
        daily_file = self._get_daily_file_path()
        
        if not daily_file.exists():
            print("No worklog entries for today.")
            return
        
        try:
            with open(daily_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            if not content:
                print("No worklog entries for today.")
                return
                
            print(f"Today's worklog ({daily_file.name}):")
            for line in content.split('\n'):
                if line.strip():
                    print(f"  {line}")
        except IOError as e:
            print(f"Error reading today's file: {e}")
    
    def show_date_file(self, date_str):
        """Show worklog file for a specific date (YYYY-MM-DD)"""
        daily_file = self._get_daily_file_path(date_str)
        
        if not daily_file.exists():
            print(f"No worklog entries for {date_str}.")
            return
        
        try:
            with open(daily_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            if not content:
                print(f"No worklog entries for {date_str}.")
                return
                
            print(f"Worklog for {date_str}:")
            for line in content.split('\n'):
                if line.strip():
                    print(f"  {line}")
        except IOError as e:
            print(f"Error reading file for {date_str}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='WorkLog CLI Tool - Track time spent on tasks',
        epilog='Examples:\n'
               '  worklog "Fix bug #123"    # Start task (stops previous)\n'
               '  worklog "Task" --start-time 09:30 # Start at specific time\n'
               '  worklog "New task" -pl   # Allow multiple tasks\n'
               '  worklog --start          # Start anonymous session\n'
               '  worklog --stop           # Stop all active/paused tasks\n'
               '  worklog -pa              # Pause all active tasks\n'
               '  worklog --resume         # Resume last paused task\n'
               '  worklog --clean          # Clean today\'s worklog\n'
               '  worklog --list           # List active tasks or today\'s log\n'
               '  worklog --recent         # Show recent entries\n'
               '  worklog --today          # Show today\'s worklog\n'
               '  worklog --date 2025-10-02 # Show specific date',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('task', nargs='?', help='Task name to start or end')
    parser.add_argument('--list', '-l', action='store_true', 
                       help='List all active tasks')
    parser.add_argument('--recent', '-r', action='store_true',
                       help='Show recent worklog entries')
    parser.add_argument('--count', '-c', type=int, default=10,
                       help='Number of recent entries to show (default: 10)')
    parser.add_argument('--today', '-t', action='store_true',
                       help='Show today\'s worklog file')
    parser.add_argument('--date', '-d', type=str,
                       help='Show worklog file for specific date (YYYY-MM-DD)')
    parser.add_argument('--start', '-s', action='store_true',
                       help='Start anonymous work session (to be named later)')
    parser.add_argument('--stop', action='store_true',
                       help='Stop all active tasks')
    parser.add_argument('--pause', '-pa', action='store_true',
                       help='Pause all active tasks (can be resumed later)')
    parser.add_argument('--resume', action='store_true',
                       help='Resume the last paused task')
    parser.add_argument('--parallel', '-pl', action='store_true',
                       help='Allow multiple concurrent tasks (default: single task mode)')
    parser.add_argument('--start-time', type=str,
                       help='Set custom start time for task (HH:MM format)')
    parser.add_argument('--clean', action='store_true',
                       help='Clean today\'s worklog (with confirmation)')
    
    args = parser.parse_args()
    
    worklog = WorkLog()
    
    if args.clean:
        worklog.clean_today_worklog()
    elif args.list:
        worklog.list_active_tasks()
    elif args.recent:
        worklog.show_recent_entries(args.count)
    elif args.today:
        worklog.show_today_file()
    elif args.date:
        worklog.show_date_file(args.date)
    elif args.start:
        # Handle custom start time for anonymous tasks
        if args.start_time:
            try:
                worklog.start_anonymous_task_at_time(args.start_time)
            except ValueError as e:
                print(f"Error: {e}")
                sys.exit(1)
        else:
            worklog.start_anonymous_task()
    elif args.stop:
        worklog.stop_all_tasks()
    elif args.pause:
        worklog.pause_all_tasks()
    elif args.resume:
        worklog.resume_last_task()
    elif args.task:
        # Validate start_time if provided
        if args.start_time:
            try:
                # Just validate the format - handle_task will use it
                worklog._parse_custom_time(args.start_time)
                worklog.handle_task(args.task, parallel_mode=args.parallel, custom_start_time=args.start_time)
            except ValueError as e:
                print(f"Error: {e}")
                sys.exit(1)
        else:
            worklog.handle_task(args.task, parallel_mode=args.parallel)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()