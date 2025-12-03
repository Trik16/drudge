#!/usr/bin/env python3
"""Clear November data rows (keep headers)."""
import sys
import yaml
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json

# Load config from dev-env/test-config.yaml
config_path = Path(__file__).parent / "test-config.yaml"
if config_path.exists():
    with open(config_path) as f:
        config = yaml.safe_load(f)
    sheet_id = config.get('sheet_document_id', '')
else:
    sheet_id = '1XgCsSSnWFoYX1DVmqRnyRlJCV4ortxGA-tquz1GlahY'

# Credentials path (check dev-env first, then /app)
creds_path = Path(__file__).parent / "credentials.json"
if not creds_path.exists():
    creds_path = Path('/app/credentials.json')

with open(creds_path, 'r') as f:
    cred_data = json.load(f)

creds = Credentials(
    token=cred_data.get('token'),
    refresh_token=cred_data.get('refresh_token'),
    token_uri=cred_data.get('token_uri'),
    client_id=cred_data.get('client_id'),
    client_secret=cred_data.get('client_secret'),
    scopes=cred_data.get('scopes')
)

service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

# Clear data rows (keep header row 1)
sheet.values().clear(
    spreadsheetId=sheet_id,
    range='November!A2:Z1000'
).execute()

print("✅ Cleared November data rows (kept headers)")
