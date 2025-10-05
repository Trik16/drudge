"""Google Sheets sync functionality for haunts-compatible format."""

import math
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

import gspread
from google.auth.exceptions import DefaultCredentialsError
from google.oauth2.service_account import Credentials

from ..config import WorkLogConfig
from ..models import TaskEntry


def round_hours(hours: float, increment: float) -> float:
    """
    Round hours to the nearest increment.
    
    Args:
        hours: The hours value to round
        increment: The rounding increment (0.25 for 15min, 0.5 for 30min, 1.0 for hour)
    
    Returns:
        Rounded hours value
    
    Examples:
        >>> round_hours(2.2, 0.25)  # 2h 12m → 2.25 (2h 15m)
        2.25
        >>> round_hours(2.6, 0.5)   # 2h 36m → 2.5 (2h 30m)
        2.5
        >>> round_hours(2.4, 1.0)   # 2h 24m → 2.0 (2h 0m)
        2.0
    """
    return round(hours / increment) * increment


def format_hours(hours: float, round_increment: float) -> str:
    """
    Format hours with rounding, using comma as decimal separator.
    
    Decimal places are automatically determined based on the rounding increment:
    - 1.0 (hour) → 0 decimals
    - 0.5 (30min) → 1 decimal
    - 0.25 (15min) → 2 decimals
    
    Args:
        hours: The hours value to format
        round_increment: Rounding increment (0.25, 0.5, or 1.0)
    
    Returns:
        Formatted hours string with comma separator (European format)
    
    Examples:
        >>> format_hours(2.2, 0.25)  # 2h 12m → "2,25"
        '2,25'
        >>> format_hours(2.6, 0.5)   # 2h 36m → "2,5"
        '2,5'
        >>> format_hours(2.4, 1.0)   # 2h 24m → "2"
        '2'
    """
    rounded = round_hours(hours, round_increment)
    
    # Determine decimal places based on increment
    if round_increment >= 1.0:
        decimal_places = 0
    elif round_increment >= 0.5:
        decimal_places = 1
    else:  # 0.25 or smaller
        decimal_places = 2
    
    if decimal_places == 0:
        return str(int(rounded))
    
    # Format with calculated decimal places
    format_str = f"{{:.{decimal_places}f}}"
    formatted = format_str.format(rounded)
    
    # Replace dot with comma for European format
    return formatted.replace(".", ",")


class GoogleSheetsSync:
    """
    Handles syncing work tasks to Google Sheets in haunts-compatible format.
    
    The sheet structure follows the haunts convention:
    - Monthly sheets named by full month name (e.g., "October", "November")
    - Columns: Date, Start time, Project, Activity, Details, Spent
    - Date format: DD/MM/YYYY
    - Time format: HH:MM
    - Duration: decimal hours with comma separator
    """
    
    def __init__(self, config: WorkLogConfig, credentials_path: Optional[Path] = None):
        """
        Initialize the Google Sheets sync.
        
        Args:
            config: WorkLog configuration
            credentials_path: Path to Google service account JSON credentials.
                            If None, uses default credentials.
        
        Raises:
            ValueError: If Google Sheets is not enabled in config
            FileNotFoundError: If credentials file doesn't exist
            DefaultCredentialsError: If authentication fails
        """
        if not config.google_sheets.enabled:
            raise ValueError("Google Sheets sync is not enabled in configuration")
        
        self.config = config
        self.credentials_path = credentials_path
        self._client: Optional[gspread.Client] = None
        self._spreadsheet: Optional[gspread.Spreadsheet] = None
    
    def _get_client(self) -> gspread.Client:
        """Get or create the gspread client."""
        if self._client is None:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive.file'
            ]
            
            if self.credentials_path:
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_path}"
                    )
                creds = Credentials.from_service_account_file(
                    str(self.credentials_path),
                    scopes=scopes
                )
                self._client = gspread.authorize(creds)
            else:
                # Try default credentials (OAuth or service account)
                try:
                    self._client = gspread.oauth()
                except Exception as e:
                    raise DefaultCredentialsError(
                        "Failed to authenticate with Google Sheets. "
                        "Please provide credentials_path or set up OAuth. "
                        f"Error: {e}"
                    )
        
        return self._client
    
    def _get_spreadsheet(self) -> gspread.Spreadsheet:
        """Get or open the configured spreadsheet."""
        if self._spreadsheet is None:
            client = self._get_client()
            try:
                self._spreadsheet = client.open_by_key(self.config.sheet_document_id)
            except gspread.exceptions.SpreadsheetNotFound:
                raise ValueError(
                    f"Spreadsheet not found with ID: {self.config.sheet_document_id}. "
                    "Please check your sheet_document_id in config."
                )
        
        return self._spreadsheet
    
    def _get_or_create_sheet(self, sheet_name: str) -> gspread.Worksheet:
        """
        Get or create a worksheet by name.
        
        Args:
            sheet_name: Name of the worksheet (e.g., "October")
        
        Returns:
            The worksheet object
        """
        spreadsheet = self._get_spreadsheet()
        
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            # Create new worksheet with headers
            worksheet = spreadsheet.add_worksheet(
                title=sheet_name,
                rows=100,
                cols=9
            )
            # Add header row
            headers = [
                "Date", "Start time", "Project", "Activity", 
                "Details", "Spent", "Event id", "Link", "Action"
            ]
            worksheet.update('A1:I1', [headers])
        
        return worksheet
    
    def _format_date(self, timestamp_str: str) -> str:
        """Format ISO timestamp string to DD/MM/YYYY."""
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime("%d/%m/%Y")
    
    def _format_time(self, timestamp_str: str) -> str:
        """Format ISO timestamp string to HH:MM."""
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime("%H:%M")
    
    def _calculate_hours(self, task: TaskEntry) -> float:
        """Calculate task duration in hours from ISO timestamp strings."""
        if task.end_time and task.start_time:
            start_dt = datetime.fromisoformat(task.start_time)
            end_dt = datetime.fromisoformat(task.end_time)
            duration_seconds = (end_dt - start_dt).total_seconds()
            return duration_seconds / 3600
        return 0.0
    
    def sync_task(self, task: TaskEntry) -> None:
        """
        Sync a single task to Google Sheets.
        
        Args:
            task: The task entry to sync
        
        Raises:
            ValueError: If task is not completed (no end_time)
        """
        if not task.end_time:
            raise ValueError("Cannot sync task without end_time")
        
        # Parse end_time to get the date for sheet selection
        end_dt = datetime.fromisoformat(task.end_time)
        sheet_date = end_dt.strftime("%Y-%m-%d")
        
        # Get the appropriate monthly sheet
        sheet_name = self.config.get_sheet_name_for_date(sheet_date)
        worksheet = self._get_or_create_sheet(sheet_name)
        
        # Calculate and format hours
        hours = self._calculate_hours(task)
        formatted_hours = format_hours(
            hours,
            self.config.google_sheets.round_hours
        )
        
        # Prepare row data
        row_data = [
            self._format_date(task.end_time),
            self._format_time(task.start_time),
            task.project or "",
            task.task,  # Use task.task for the task name
            task.description or "",
            formatted_hours,
            "",  # Event id (filled by haunts)
            "",  # Link (filled by haunts)
            ""   # Action (used by haunts)
        ]
        
        # Append to worksheet
        worksheet.append_row(row_data, value_input_option='USER_ENTERED')
    
    def sync_tasks(self, tasks: List[TaskEntry], filter_date: Optional[date] = None) -> int:
        """
        Sync multiple tasks to Google Sheets.
        
        Args:
            tasks: List of task entries to sync
            filter_date: If provided, only sync tasks from this date
        
        Returns:
            Number of tasks synced
        
        Raises:
            ValueError: If any task is not completed
        """
        synced_count = 0
        
        for task in tasks:
            if not task.end_time:
                continue  # Skip incomplete tasks
            
            # Filter by date if specified
            if filter_date:
                end_dt = datetime.fromisoformat(task.end_time)
                if end_dt.date() != filter_date:
                    continue
            
            self.sync_task(task)
            synced_count += 1
        
        return synced_count
    
    def test_connection(self) -> bool:
        """
        Test the connection to Google Sheets.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            spreadsheet = self._get_spreadsheet()
            # Try to access spreadsheet title to verify access
            _ = spreadsheet.title
            return True
        except Exception:
            return False
    
    def sync_daily(self, dry_run: bool = False) -> dict:
        """
        Sync today's completed tasks to Google Sheets.
        
        Args:
            dry_run: If True, simulate sync without writing to sheets
        
        Returns:
            Dictionary with sync results (count, sheets_updated)
        """
        from ..managers.worklog import WorkLog
        
        worklog = WorkLog(config=self.config)
        today = datetime.now().date()
        
        # Filter completed tasks from today
        completed_tasks = [
            task for task in worklog.data.entries
            if task.end_time and datetime.fromisoformat(task.end_time).date() == today
        ]
        
        if dry_run:
            return {
                'count': len(completed_tasks),
                'sheets_updated': [self.config.get_sheet_name_for_date(today.strftime("%Y-%m-%d"))]
            }
        
        synced = self.sync_tasks(completed_tasks, filter_date=today)
        return {
            'count': synced,
            'sheets_updated': [self.config.get_sheet_name_for_date(today.strftime("%Y-%m-%d"))]
        }
    
    def sync_monthly(self, dry_run: bool = False) -> dict:
        """
        Sync current month's completed tasks to Google Sheets.
        
        Args:
            dry_run: If True, simulate sync without writing to sheets
        
        Returns:
            Dictionary with sync results (count, sheets_updated)
        """
        from ..managers.worklog import WorkLog
        
        worklog = WorkLog(config=self.config)
        now = datetime.now()
        current_month = now.month
        current_year = now.year
        
        # Filter completed tasks from current month
        completed_tasks = [
            task for task in worklog.data.entries
            if task.end_time and 
            datetime.fromisoformat(task.end_time).month == current_month and
            datetime.fromisoformat(task.end_time).year == current_year
        ]
        
        if dry_run:
            sheet_name = self.config.get_sheet_name_for_date(now.strftime("%Y-%m-%d"))
            return {
                'count': len(completed_tasks),
                'sheets_updated': [sheet_name]
            }
        
        synced = self.sync_tasks(completed_tasks)
        sheet_name = self.config.get_sheet_name_for_date(now.strftime("%Y-%m-%d"))
        return {
            'count': synced,
            'sheets_updated': [sheet_name]
        }
    
    def sync_date(self, date_str: str, dry_run: bool = False) -> dict:
        """
        Sync tasks from a specific date to Google Sheets.
        
        Args:
            date_str: Date in YYYY-MM-DD format
            dry_run: If True, simulate sync without writing to sheets
        
        Returns:
            Dictionary with sync results (count, sheets_updated)
        
        Raises:
            ValueError: If date format is invalid
        """
        from ..managers.worklog import WorkLog
        
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError as e:
            raise ValueError(f"Invalid date format. Use YYYY-MM-DD: {e}")
        
        worklog = WorkLog(config=self.config)
        
        # Filter completed tasks from target date
        completed_tasks = [
            task for task in worklog.data.entries
            if task.end_time and datetime.fromisoformat(task.end_time).date() == target_date
        ]
        
        if dry_run:
            return {
                'count': len(completed_tasks),
                'sheets_updated': [self.config.get_sheet_name_for_date(date_str)]
            }
        
        synced = self.sync_tasks(completed_tasks, filter_date=target_date)
        return {
            'count': synced,
            'sheets_updated': [self.config.get_sheet_name_for_date(date_str)]
        }
    
    def sync_all(self, dry_run: bool = False) -> dict:
        """
        Sync all completed tasks to Google Sheets.
        
        Args:
            dry_run: If True, simulate sync without writing to sheets
        
        Returns:
            Dictionary with sync results (count, sheets_updated)
        """
        from ..managers.worklog import WorkLog
        
        worklog = WorkLog(config=self.config)
        
        # Get all completed tasks
        completed_tasks = [
            task for task in worklog.data.entries
            if task.end_time
        ]
        
        if dry_run:
            # Get unique months from completed tasks
            sheets_updated = list(set(
                self.config.get_sheet_name_for_date(
                    datetime.fromisoformat(task.end_time).strftime("%Y-%m-%d")
                )
                for task in completed_tasks
            ))
            return {
                'count': len(completed_tasks),
                'sheets_updated': sorted(sheets_updated)
            }
        
        synced = self.sync_tasks(completed_tasks)
        
        # Get unique months from synced tasks
        sheets_updated = list(set(
            self.config.get_sheet_name_for_date(
                datetime.fromisoformat(task.end_time).strftime("%Y-%m-%d")
            )
            for task in completed_tasks
        ))
        
        return {
            'count': synced,
            'sheets_updated': sorted(sheets_updated)
        }
