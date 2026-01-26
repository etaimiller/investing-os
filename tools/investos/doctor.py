"""
Repository health checks ("doctor" command)

Verifies expected directory structure, required files, and data validity.
Provides actionable feedback on what needs fixing.
"""

from pathlib import Path
from typing import List, Tuple
from .utils import is_valid_json
from .config import Config
from .validate import validate_with_schema, JSONSCHEMA_AVAILABLE


class HealthCheck:
    """Repository health check results"""
    
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []
        self.errors = []
        self.info = []
    
    def pass_check(self, message: str) -> None:
        """Record passed check"""
        self.checks_passed += 1
        self.info.append(f"✓ {message}")
    
    def fail_check(self, message: str) -> None:
        """Record failed check"""
        self.checks_failed += 1
        self.errors.append(f"✗ {message}")
    
    def warn(self, message: str) -> None:
        """Record warning"""
        self.warnings.append(f"⚠ {message}")
    
    @property
    def is_healthy(self) -> bool:
        """Overall health status"""
        return self.checks_failed == 0
    
    def summary(self) -> str:
        """Generate summary report"""
        lines = []
        lines.append("=" * 60)
        lines.append("Investment OS Health Check")
        lines.append("=" * 60)
        lines.append("")
        
        # Summary
        lines.append(f"Checks passed: {self.checks_passed}")
        lines.append(f"Checks failed: {self.checks_failed}")
        lines.append(f"Warnings: {len(self.warnings)}")
        lines.append("")
        
        # Errors (if any)
        if self.errors:
            lines.append("ERRORS:")
            for error in self.errors:
                lines.append(f"  {error}")
            lines.append("")
        
        # Warnings (if any)
        if self.warnings:
            lines.append("WARNINGS:")
            for warning in self.warnings:
                lines.append(f"  {warning}")
            lines.append("")
        
        # Info
        if self.info:
            lines.append("CHECKS:")
            for info in self.info:
                lines.append(f"  {info}")
            lines.append("")
        
        # Overall status
        if self.is_healthy:
            lines.append("Status: HEALTHY ✓")
        else:
            lines.append("Status: NEEDS ATTENTION ✗")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)


def check_directory_structure(repo_root: Path, health: HealthCheck) -> None:
    """Check expected directories exist"""
    expected_dirs = [
        'portfolio',
        'portfolio/raw',
        'portfolio/snapshots',
        'research',
        'valuations',
        'valuations/assumptions',
        'decisions',
        'monitoring',
        'playbooks',
        'logs',
        'logs/runs',
        'tools',
        'skills',
        'schema',
    ]
    
    for dir_path in expected_dirs:
        full_path = repo_root / dir_path
        if full_path.exists():
            health.pass_check(f"Directory exists: {dir_path}")
        else:
            health.fail_check(f"Missing directory: {dir_path}")


def check_required_files(repo_root: Path, health: HealthCheck) -> None:
    """Check required files exist"""
    required_files = [
        'agents.md',
        'MANIFEST.md',
        'README.md',
        'config.json',
        '.gitignore',
    ]
    
    for file_path in required_files:
        full_path = repo_root / file_path
        if full_path.exists():
            health.pass_check(f"Required file exists: {file_path}")
        else:
            health.fail_check(f"Missing required file: {file_path}")


def check_schema_files(repo_root: Path, config: Config, health: HealthCheck) -> None:
    """Check schema files exist and are valid JSON"""
    schema_dir = repo_root / config.schema_dir
    
    expected_schemas = [
        'portfolio-state.schema.json',
        'valuation-model.schema.json',
        'decision-memo.schema.json',
    ]
    
    for schema_file in expected_schemas:
        schema_path = schema_dir / schema_file
        if not schema_path.exists():
            health.fail_check(f"Missing schema: {schema_file}")
            continue
        
        if is_valid_json(schema_path):
            health.pass_check(f"Valid schema: {schema_file}")
        else:
            health.fail_check(f"Invalid JSON in schema: {schema_file}")


def check_config_file(repo_root: Path, health: HealthCheck) -> None:
    """Check config.json is valid"""
    config_path = repo_root / 'config.json'
    
    if not config_path.exists():
        health.fail_check("config.json not found")
        return
    
    if is_valid_json(config_path):
        health.pass_check("config.json is valid JSON")
    else:
        health.fail_check("config.json contains invalid JSON")


def check_portfolio_snapshots(repo_root: Path, config: Config, health: HealthCheck) -> None:
    """Check portfolio snapshots for validity and schema compliance"""
    snapshots_dir = repo_root / config.snapshots_dir
    
    if not snapshots_dir.exists():
        health.warn("No snapshots directory found (expected for new repo)")
        return
    
    json_files = list(snapshots_dir.glob('*.json'))
    
    if not json_files:
        health.warn("No portfolio snapshots found (expected for new repo)")
        return
    
    # Get schema path
    schema_path = repo_root / config.schema_dir / 'portfolio-state.schema.json'
    
    for json_file in json_files:
        # First check valid JSON
        if not is_valid_json(json_file):
            health.fail_check(f"Invalid JSON in snapshot: {json_file.name}")
            continue
        
        # Then validate against schema if jsonschema available
        if JSONSCHEMA_AVAILABLE and schema_path.exists():
            result = validate_with_schema(json_file, schema_path)
            if result.valid:
                health.pass_check(f"Valid snapshot (schema-compliant): {json_file.name}")
            else:
                health.fail_check(f"Schema validation failed: {json_file.name}")
                for error in result.errors[:3]:  # Show first 3 errors
                    health.warn(f"  {error}")
        else:
            # Basic validation only
            health.pass_check(f"Valid JSON snapshot: {json_file.name}")
            if not JSONSCHEMA_AVAILABLE:
                health.warn("jsonschema not installed - schema validation skipped")


def run_health_check(repo_root: Path, config: Config) -> HealthCheck:
    """Run complete health check"""
    health = HealthCheck()
    
    # Run all checks
    check_directory_structure(repo_root, health)
    check_required_files(repo_root, health)
    check_config_file(repo_root, health)
    check_schema_files(repo_root, config, health)
    check_portfolio_snapshots(repo_root, config, health)
    
    return health
