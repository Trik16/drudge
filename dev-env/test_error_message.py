#!/usr/bin/env python3
"""Test error message when use_haunts_format is disabled."""
import sys
from pathlib import Path
from worklog.config import WorkLogConfig
from worklog.sync.sheets import GoogleSheetsSync

# Load config
config = WorkLogConfig.load_from_yaml(Path("/app/test-config.yaml"))

# Disable haunts format
config.google_sheets.use_haunts_format = False

print("Testing with use_haunts_format=False...")
print(f"Config: use_haunts_format={config.google_sheets.use_haunts_format}")

try:
    sync = GoogleSheetsSync(config, Path("/app/credentials.json"))
    print("✅ GoogleSheetsSync initialized (using gspread fallback)")
except ValueError as e:
    print(f"❌ ValueError (expected): {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
