"""
Configuration management for WorkLog CLI Tool.

This module provides centralized configuration with sensible defaults,
YAML configuration file support, and haunts integration settings.
"""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional, List


@dataclass
class GoogleSheetsConfig:
    """
    Configuration for Google Sheets sync (haunts-compatible format).
    
    Attributes:
        enabled: Whether Google Sheets sync is enabled
        auto_sync: Automatically sync to Google Sheet when ending tasks
        round_hours: Rounding increment in hours (0.25=15min, 0.5=30min, 1.0=hour, default 0.5)
        use_haunts_format: Use haunts-compatible format (DD/MM/YYYY, HH:MM, comma decimal) instead of gspread
        sheet_language: Language for sheet tab names ('en' for English, 'it' for Italian)
    """
    enabled: bool = False
    auto_sync: bool = False
    round_hours: float = 0.5  # 0.25 (15min), 0.5 (30min), 1.0 (hour)
    use_haunts_format: bool = True  # Default to haunts format for consistency
    sheet_language: str = "en"  # 'en' for English, 'it' for Italian


# Month names mapping for different languages
MONTH_NAMES = {
    "en": ["January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"],
    "it": ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
           "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"],
}


@dataclass
class HauntsConfig:
    """
    Optional reference to Haunts integration (for Calendar sync).
    
    This is purely informational - the actual sync happens via Google Sheets.
    Haunts reads the sheet and creates Calendar events.
    
    Attributes:
        enabled: Whether you use Haunts for Calendar sync
        config_path: Path to haunts configuration directory (reference only)
    """
    enabled: bool = False
    config_path: str = "~/.haunts"


@dataclass
class WorkLogConfig:
    """
    Configuration settings for WorkLog with sensible defaults.
    
    Centralizes all configurable options for the worklog system,
    allowing users to customize behavior without code changes.
    Supports YAML configuration file for persistent settings.
    
    Attributes:
        worklog_dir_name: Name of the worklog directory
        worklog_dir: Optional override for custom directory path (for testing)
        date_format: Date format string for parsing and display
        time_format: Time format string for parsing user input
        display_time_format: Format for displaying timestamps to users
        max_recent_tasks: Maximum number of recent tasks to remember
        backup_enabled: Whether to create backups before destructive operations
        auto_save: Whether to automatically save after each operation
        max_backups: Maximum number of backup files to retain
        sheet_document_id: Google Sheets document ID (shared by drudge and haunts)
        timezone: Timezone for timestamps (from haunts or system default)
        projects: List of project names for categorization
        google_sheets: Google Sheets sync configuration
        haunts: Optional Haunts integration reference
    """
    worklog_dir_name: str = '.worklog'
    worklog_dir: str = None  # Optional override for custom directory path
    date_format: str = "%Y-%m-%d"
    time_format: str = "%H:%M"
    display_time_format: str = "%Y-%m-%d %H:%M:%S"
    max_recent_tasks: int = 10
    backup_enabled: bool = True
    auto_save: bool = True
    max_backups: int = 5
    sheet_document_id: str = ""  # Shared Google Sheets document ID
    timezone: str = ""  # From haunts.ini or system default
    projects: List[str] = field(default_factory=list)  # Project names only
    google_sheets: GoogleSheetsConfig = field(default_factory=GoogleSheetsConfig)
    haunts: HauntsConfig = field(default_factory=HauntsConfig)
    
    @classmethod
    def load_from_yaml(cls, config_path: Optional[Path] = None) -> 'WorkLogConfig':
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to config file. If None, uses default ~/.worklog/config.yaml
            
        Returns:
            WorkLogConfig instance with values from YAML file or defaults
        """
        if config_path is None:
            config_path = Path.home() / '.worklog' / 'config.yaml'
        
        if not config_path.exists():
            # Return default config if file doesn't exist
            return cls()
        
        try:
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f) or {}
            
            # Handle nested google_sheets config
            google_sheets_data = data.pop('google_sheets', {})
            # Remove unknown fields for testing compatibility
            google_sheets_data.pop('credentials_file', None)
            google_sheets_data.pop('document_id', None)
            google_sheets_config = GoogleSheetsConfig(**google_sheets_data) if google_sheets_data else GoogleSheetsConfig()
            
            # Handle nested haunts config
            haunts_data = data.pop('haunts', {})
            haunts_config = HauntsConfig(**haunts_data) if haunts_data else HauntsConfig()
            
            # Create config with loaded data
            return cls(**data, google_sheets=google_sheets_config, haunts=haunts_config)
        except Exception as e:
            # If there's an error loading, return defaults and log warning
            print(f"Warning: Could not load config from {config_path}: {e}")
            return cls()
    
    def save_to_yaml(self, config_path: Optional[Path] = None) -> None:
        """
        Save configuration to YAML file.
        
        Args:
            config_path: Path to config file. If None, uses default ~/.worklog/config.yaml
        """
        if config_path is None:
            config_path = Path.home() / '.worklog' / 'config.yaml'
        
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict and handle nested dataclasses
        data = asdict(self)
        
        # Remove None worklog_dir (internal testing override)
        if data['worklog_dir'] is None:
            data.pop('worklog_dir')
        
        with open(config_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    def get_worklog_directory(self) -> Path:
        """Get the worklog directory path."""
        if self.worklog_dir:
            return Path(self.worklog_dir)
        return Path.home() / self.worklog_dir_name
    
    def add_project(self, project_name: str) -> None:
        """Add a new project to the list."""
        if project_name not in self.projects:
            self.projects.append(project_name)
    
    def remove_project(self, project_name: str) -> None:
        """Remove a project from the list."""
        if project_name in self.projects:
            self.projects.remove(project_name)
    
    def get_all_projects(self) -> List[str]:
        """Get list of all configured project names."""
        return self.projects
    
    def get_sheet_name_for_date(self, date: str) -> str:
        """
        Auto-calculate Google Sheet tab name from date.
        
        Args:
            date: Date string in format YYYY-MM-DD
            
        Returns:
            Month name in configured language (e.g., "October", "Ottobre")
        """
        from datetime import datetime
        dt = datetime.strptime(date, "%Y-%m-%d")
        month_index = dt.month - 1  # 0-based index
        language = self.google_sheets.sheet_language
        
        if language in MONTH_NAMES:
            return MONTH_NAMES[language][month_index]
        else:
            # Fallback to English if language not supported
            return MONTH_NAMES["en"][month_index]