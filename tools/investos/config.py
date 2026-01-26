"""
Configuration loader for Investment OS

Reads config.json from repo root and provides typed access to settings.
Uses stdlib only - no external dependencies.
"""

import json
from pathlib import Path
from typing import Dict, Any


class Config:
    """Investment OS configuration"""
    
    def __init__(self, config_path: Path):
        """Load configuration from JSON file"""
        self.config_path = config_path
        self.data = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load and parse config.json"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    @property
    def version(self) -> str:
        return self.data.get('version', '1.0.0')
    
    @property
    def timezone(self) -> str:
        return self.data.get('timezone', 'Africa/Johannesburg')
    
    @property
    def base_currency(self) -> str:
        return self.data.get('base_currency', 'EUR')
    
    @property
    def portfolio_raw_dir(self) -> str:
        return self.data.get('portfolio', {}).get('raw_dir', 'portfolio/raw')
    
    @property
    def snapshots_dir(self) -> str:
        return self.data.get('portfolio', {}).get('snapshots_dir', 'portfolio/snapshots')
    
    @property
    def schema_dir(self) -> str:
        return self.data.get('schema_dir', 'schema')
    
    @property
    def default_assumptions_file(self) -> str:
        return self.data.get('valuations', {}).get('default_assumptions_file', 
                                                     'valuations/assumptions/conservative.yaml')
    
    @property
    def watch_rules_file(self) -> str:
        return self.data.get('monitoring', {}).get('watch_rules_file', 
                                                    'monitoring/watch_rules.yaml')
    
    @property
    def logs_dir(self) -> str:
        return self.data.get('logs', {}).get('runs_dir', 'logs/runs')


def load_config(repo_root: Path) -> Config:
    """Load config from repo root"""
    config_path = repo_root / 'config.json'
    return Config(config_path)
