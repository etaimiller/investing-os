"""
Utility functions for Investment OS CLI

Common helper functions used across CLI commands.
Uses stdlib only.
"""

from pathlib import Path
from typing import List, Optional
import json


def find_repo_root() -> Path:
    """
    Find the repository root by looking for key files.
    Walks up from current directory until it finds agents.md or MANIFEST.md
    """
    current = Path.cwd()
    
    # Check current directory first
    if (current / 'agents.md').exists() or (current / 'MANIFEST.md').exists():
        return current
    
    # Walk up parents
    for parent in current.parents:
        if (parent / 'agents.md').exists() or (parent / 'MANIFEST.md').exists():
            return parent
    
    # Fallback to current directory
    return current


def count_files(directory: Path, pattern: str = '*') -> int:
    """Count files matching pattern in directory"""
    if not directory.exists():
        return 0
    return len(list(directory.glob(pattern)))


def find_latest_file(directory: Path, pattern: str = '*') -> Optional[Path]:
    """Find most recently modified file matching pattern"""
    if not directory.exists():
        return None
    
    files = list(directory.glob(pattern))
    if not files:
        return None
    
    return max(files, key=lambda p: p.stat().st_mtime)


def is_valid_json(file_path: Path) -> bool:
    """Check if file contains valid JSON"""
    try:
        with open(file_path, 'r') as f:
            json.load(f)
        return True
    except (json.JSONDecodeError, IOError):
        return False


def read_json(file_path: Path) -> dict:
    """Read and parse JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)


def ensure_dir(directory: Path) -> None:
    """Ensure directory exists, creating it if necessary"""
    directory.mkdir(parents=True, exist_ok=True)


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def get_directory_size(directory: Path) -> int:
    """Calculate total size of files in directory (non-recursive)"""
    if not directory.exists():
        return 0
    total_size = sum(f.stat().st_size for f in directory.iterdir() if f.is_file())
    return int(total_size)
