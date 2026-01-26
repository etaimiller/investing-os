"""
Structured logging for Investment OS

All CLI operations write structured JSON logs to logs/runs/
Format: logs/runs/YYYY-MM-DD/HHMMSS_<command>.json

Logs are machine-readable and provide audit trail for all operations.
They do NOT replace decision memos or analysis documentation.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import time


class RunLogger:
    """Structured logger for CLI runs"""
    
    def __init__(self, repo_root: Path, logs_dir: str, command: str, args: List[str]):
        """Initialize logger for a CLI run"""
        self.repo_root = repo_root
        self.logs_dir = repo_root / logs_dir
        self.command = command
        self.args = args
        self.start_time = time.time()
        self.timestamp = datetime.now(timezone.utc)
        
        # Log data structure
        self.log_data: Dict[str, Any] = {
            'timestamp': self.timestamp.isoformat(),
            'command': command,
            'args': args,
            'repo_root': str(repo_root),
            'paths_touched': [],
            'outcome': 'pending',
            'errors': [],
            'warnings': [],
            'info': {},
            'duration_ms': 0
        }
        
    def add_path(self, path: Path) -> None:
        """Record a path that was accessed or modified"""
        rel_path = str(path.relative_to(self.repo_root) if path.is_absolute() else path)
        if rel_path not in self.log_data['paths_touched']:
            self.log_data['paths_touched'].append(rel_path)
    
    def add_error(self, error: str) -> None:
        """Record an error"""
        self.log_data['errors'].append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'message': error
        })
    
    def add_warning(self, warning: str) -> None:
        """Record a warning"""
        self.log_data['warnings'].append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'message': warning
        })
    
    def set_info(self, key: str, value: Any) -> None:
        """Set additional information"""
        self.log_data['info'][key] = value
    
    def success(self, message: Optional[str] = None) -> None:
        """Mark run as successful"""
        self.log_data['outcome'] = 'success'
        if message:
            self.set_info('success_message', message)
    
    def failure(self, message: Optional[str] = None) -> None:
        """Mark run as failed"""
        self.log_data['outcome'] = 'failure'
        if message:
            self.add_error(message)
    
    def write(self) -> Path:
        """Write log to disk and return log file path"""
        # Calculate duration
        self.log_data['duration_ms'] = int((time.time() - self.start_time) * 1000)
        
        # Create logs directory structure: logs/runs/YYYY-MM-DD/
        date_dir = self.logs_dir / self.timestamp.strftime('%Y-%m-%d')
        date_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate log filename: HHMMSS_<command>.json
        time_prefix = self.timestamp.strftime('%H%M%S')
        log_filename = f"{time_prefix}_{self.command}.json"
        log_path = date_dir / log_filename
        
        # Write structured log
        with open(log_path, 'w') as f:
            json.dump(self.log_data, f, indent=2, default=str)
        
        return log_path


def create_logger(repo_root: Path, logs_dir: str, command: str, args: List[str]) -> RunLogger:
    """Create a new run logger"""
    return RunLogger(repo_root, logs_dir, command, args)
