#!/usr/bin/env python3
"""
Create mockup tasks for November testing

Creates several tasks across different projects for November 2025
to test the sync functionality with real data.
"""

import sys
import yaml
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path (parent directory since we're in dev-env/)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from worklog.managers.worklog import WorkLog
from worklog.config import WorkLogConfig
from worklog.models import TaskEntry, WorkLogData


def load_test_config():
    """Load test configuration."""
    # Look for config in same directory (dev-env/)
    config_path = Path(__file__).parent / "test-config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"test-config.yaml not found at {config_path}")
    
    with open(config_path) as f:
        return yaml.safe_load(f)


def create_november_tasks():
    """Create mockup tasks for November 2025."""
    config = load_test_config()
    
    # Setup worklog
    worklog_dir = config.get("worklog_dir", "/tmp/test-worklog")
    Path(worklog_dir).mkdir(parents=True, exist_ok=True)
    Path(f"{worklog_dir}/daily").mkdir(exist_ok=True)
    
    wl_config = WorkLogConfig()
    wl_config.worklog_dir = worklog_dir
    
    # Projects from test config
    projects = config.get("projects", ["pippo", "pluto", "topolino"])
    
    # Create tasks for different days in November
    tasks = [
        # November 18, 2025 (Monday)
        {
            "date": "2025-11-18",
            "start": "09:00",
            "end": "11:30",
            "project": projects[0],  # pippo
            "task": "Setup development environment",
            "description": "Configured IDE and dependencies"
        },
        {
            "date": "2025-11-18",
            "start": "11:30",
            "end": "13:00",
            "project": projects[1],  # pluto
            "task": "Code review",
            "description": "Reviewed PR #123 for authentication module"
        },
        {
            "date": "2025-11-18",
            "start": "14:00",
            "end": "16:45",
            "project": projects[0],  # pippo
            "task": "Implement login feature",
            "description": "Added OAuth2 authentication"
        },
        
        # November 19, 2025 (Tuesday)
        {
            "date": "2025-11-19",
            "start": "09:15",
            "end": "12:00",
            "project": projects[2],  # topolino
            "task": "Database migration",
            "description": "Upgraded to PostgreSQL 15"
        },
        {
            "date": "2025-11-19",
            "start": "13:00",
            "end": "15:30",
            "project": projects[1],  # pluto
            "task": "Bug fixing",
            "description": "Fixed memory leak in worker process"
        },
        {
            "date": "2025-11-19",
            "start": "15:45",
            "end": "17:00",
            "project": projects[2],  # topolino
            "task": "Documentation",
            "description": "Updated API documentation"
        },
        
        # November 20, 2025 (Wednesday)
        {
            "date": "2025-11-20",
            "start": "09:00",
            "end": "10:30",
            "project": projects[0],  # pippo
            "task": "Team meeting",
            "description": "Sprint planning for next iteration"
        },
        {
            "date": "2025-11-20",
            "start": "10:45",
            "end": "13:15",
            "project": projects[1],  # pluto
            "task": "Feature implementation",
            "description": "Added real-time notifications"
        },
        {
            "date": "2025-11-20",
            "start": "14:00",
            "end": "17:30",
            "project": projects[0],  # pippo
            "task": "Testing",
            "description": "Wrote unit tests for auth module"
        },
        
        # November 21, 2025 (Today)
        {
            "date": "2025-11-21",
            "start": "09:00",
            "end": "11:00",
            "project": projects[2],  # topolino
            "task": "Refactoring",
            "description": "Improved error handling"
        },
        {
            "date": "2025-11-21",
            "start": "11:15",
            "end": "12:45",
            "project": projects[1],  # pluto
            "task": "Performance optimization",
            "description": "Optimized database queries"
        },
    ]
    
    # Create TaskEntry objects
    entries = []
    for task_data in tasks:
        start_time = f"{task_data['date']}T{task_data['start']}:00"
        end_time = f"{task_data['date']}T{task_data['end']}:00"
        
        # TaskEntry doesn't have description field, only: task, start_time, end_time, duration, project
        entry = TaskEntry(
            task=f"{task_data['task']} - {task_data['description']}",
            start_time=start_time,
            end_time=end_time,
            project=task_data['project']
        )
        entries.append(entry)
    
    # Save to worklog
    worklog_data = WorkLogData(entries=entries)
    
    # Write to daily file for November 21 (today)
    daily_file = Path(worklog_dir) / "daily" / "2025-11-21.yaml"
    import json
    
    # Convert to dict for YAML
    data_dict = {
        'entries': [
            {
                'task': e.task,
                'start_time': e.start_time,
                'end_time': e.end_time,
                'project': e.project
            }
            for e in entries
        ]
    }
    
    with open(daily_file, 'w') as f:
        yaml.dump(data_dict, f, default_flow_style=False, allow_unicode=True)
    
    print(f"✅ Created {len(entries)} mockup tasks for November 2025")
    print(f"   Worklog file: {daily_file}")
    print(f"\nTasks by project:")
    
    for project in projects:
        count = sum(1 for e in entries if e.project == project)
        total_hours = sum(
            (datetime.fromisoformat(e.end_time) - datetime.fromisoformat(e.start_time)).total_seconds() / 3600
            for e in entries if e.project == project
        )
        print(f"   {project}: {count} tasks, {total_hours:.1f} hours")
    
    print(f"\nTotal: {len(entries)} tasks")
    
    return entries


if __name__ == "__main__":
    create_november_tasks()
