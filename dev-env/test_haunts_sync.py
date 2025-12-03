#!/usr/bin/env python3
"""
Test haunts sync with November mockup data

Usage:
    python test_haunts_sync.py [credentials_path]
    
    credentials_path: Path to OAuth token or Service Account JSON (default: /app/credentials.json)
"""

import sys
import yaml
from datetime import datetime
from pathlib import Path

# Add src to path (parent directory since we're in dev-env/)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from worklog.config import WorkLogConfig
from worklog.sync.sheets import GoogleSheetsSync
from worklog.models import TaskEntry


def load_mockup_tasks():
    """Load mockup tasks from test worklog."""
    worklog_file = Path("/tmp/test-worklog/daily/2025-11-21.yaml")
    
    if not worklog_file.exists():
        print("❌ Mockup tasks not found!")
        print("   Run: python /app/create_november_tasks.py first")
        sys.exit(1)
    
    with open(worklog_file) as f:
        data = yaml.safe_load(f)
    
    entries = []
    for e in data['entries']:
        entry = TaskEntry(
            task=e['task'],
            start_time=e['start_time'],
            end_time=e.get('end_time'),
            project=e.get('project')
        )
        entries.append(entry)
    
    return entries


def test_haunts_sync():
    """Test sync with HauntsAdapter."""
    print("🧪 Testing HauntsAdapter with November mockup data\n")
    
    # Get credentials path from CLI or default
    credentials_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/app/credentials.json")
    
    # Load mockup tasks
    entries = load_mockup_tasks()
    print(f"✅ Loaded {len(entries)} mockup tasks")
    
    # Group by project
    by_project = {}
    for e in entries:
        proj = e.project or "no-project"
        by_project[proj] = by_project.get(proj, 0) + 1
    
    print("\n📊 Tasks by project:")
    for proj, count in sorted(by_project.items()):
        print(f"   {proj}: {count} tasks")
    
    # Load config from dev-env/test-config.yaml
    config_path = Path("/app/dev-env/test-config.yaml")
    if config_path.exists():
        config = WorkLogConfig.load_from_yaml(config_path)
        print(f"\n✅ Loaded config from {config_path}")
    else:
        print(f"\n⚠️  Config not found at {config_path}, using defaults")
        config = WorkLogConfig()
        config.google_sheets.enabled = True
    
    print(f"   sheet_document_id: {config.sheet_document_id}")
    print(f"   use_haunts_format: {config.google_sheets.use_haunts_format}")
    
    # Check credentials
    if not credentials_path.exists():
        print(f"\n❌ Credentials file not found: {credentials_path}")
        sys.exit(1)
    
    print(f"\n📁 Using credentials: {credentials_path}")
    
    # Initialize GoogleSheetsSync
    try:
        sync = GoogleSheetsSync(config=config, credentials_path=credentials_path)
        print(f"✅ GoogleSheetsSync initialized")
        print(f"   Adapter present: {sync._adapter is not None}")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        sys.exit(1)
    
    # Test connection
    print("\n🔌 Testing connection...")
    try:
        if sync.test_connection():
            print("✅ Connection successful!")
        else:
            print("❌ Connection failed!")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Connection error: {e}")
        sys.exit(1)
    
    # Sync tasks
    print(f"\n🔄 Syncing {len(entries)} tasks to Google Sheets...")
    
    try:
        synced_count = sync.sync_tasks(entries)
        print(f"✅ Successfully synced {synced_count} tasks!")
        
        print("\n📝 Synced tasks:")
        for entry in entries:
            start_dt = datetime.fromisoformat(entry.start_time)
            end_dt = datetime.fromisoformat(entry.end_time)
            duration = (end_dt - start_dt).total_seconds() / 3600
            print(f"   {start_dt.strftime('%d/%m %H:%M')} | {entry.project:10s} | {duration:4.1f}h | {entry.task}")
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    test_haunts_sync()
