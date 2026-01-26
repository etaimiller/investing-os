"""
JSON validation for Investment OS

Provides full JSON Schema Draft-07 validation using jsonschema library.
Falls back to basic validation if jsonschema not installed.

Validates:
- File is valid JSON
- Data conforms to JSON Schema (if schema provided)
- Required top-level keys are present (basic mode)
- Basic type checking for known fields (basic mode)
"""

from pathlib import Path
from typing import Dict, Any, List
import json

try:
    import jsonschema
    from jsonschema import Draft7Validator, validators
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    jsonschema = None
    JSONSCHEMA_AVAILABLE = False


class ValidationResult:
    """Result of validation check"""
    
    def __init__(self, valid: bool, errors: List[str], warnings: List[str]):
        self.valid = valid
        self.errors = errors
        self.warnings = warnings
    
    def __bool__(self) -> bool:
        return self.valid
    
    def summary(self) -> str:
        """Generate validation summary"""
        lines = []
        
        if self.valid:
            lines.append("✓ Validation PASSED")
        else:
            lines.append("✗ Validation FAILED")
        
        if self.errors:
            lines.append("\nErrors:")
            for error in self.errors:
                lines.append(f"  - {error}")
        
        if self.warnings:
            lines.append("\nWarnings:")
            for warning in self.warnings:
                lines.append(f"  - {warning}")
        
        return "\n".join(lines)


def validate_json_file(file_path: Path) -> ValidationResult:
    """Validate that file contains valid JSON"""
    errors = []
    warnings = []
    
    if not file_path.exists():
        errors.append(f"File does not exist: {file_path}")
        return ValidationResult(False, errors, warnings)
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return ValidationResult(True, errors, warnings)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON: {e}")
        return ValidationResult(False, errors, warnings)
    except IOError as e:
        errors.append(f"Cannot read file: {e}")
        return ValidationResult(False, errors, warnings)


def validate_portfolio_snapshot(data: Dict[str, Any]) -> ValidationResult:
    """
    Basic validation for portfolio snapshot.
    
    Note: This is NOT full JSON Schema validation.
    Full schema validation will be enabled in Step 4/5 with jsonschema library.
    """
    errors = []
    warnings = []
    
    # Check required top-level keys
    required_keys = ['snapshot_id', 'timestamp', 'version', 'accounts', 'holdings', 'cash', 'totals']
    for key in required_keys:
        if key not in data:
            errors.append(f"Missing required field: {key}")
    
    # Basic type checks
    if 'snapshot_id' in data and not isinstance(data['snapshot_id'], str):
        errors.append("Field 'snapshot_id' must be a string")
    
    if 'accounts' in data and not isinstance(data['accounts'], list):
        errors.append("Field 'accounts' must be an array")
    
    if 'holdings' in data and not isinstance(data['holdings'], list):
        errors.append("Field 'holdings' must be an array")
    
    if 'cash' in data and not isinstance(data['cash'], list):
        errors.append("Field 'cash' must be an array")
    
    if 'totals' in data and not isinstance(data['totals'], dict):
        errors.append("Field 'totals' must be an object")
    
    # Warnings for recommended fields
    if 'metadata' not in data:
        warnings.append("Recommended field 'metadata' is missing")
    
    valid = len(errors) == 0
    return ValidationResult(valid, errors, warnings)


def validate_valuation_model(data: Dict[str, Any]) -> ValidationResult:
    """Basic validation for valuation model"""
    errors = []
    warnings = []
    
    required_keys = ['valuation_id', 'timestamp', 'security_id', 'version', 'assumptions', 'valuation']
    for key in required_keys:
        if key not in data:
            errors.append(f"Missing required field: {key}")
    
    if 'assumptions' in data and not isinstance(data['assumptions'], dict):
        errors.append("Field 'assumptions' must be an object")
    
    if 'valuation' in data and not isinstance(data['valuation'], dict):
        errors.append("Field 'valuation' must be an object")
    
    valid = len(errors) == 0
    return ValidationResult(valid, errors, warnings)


def validate_decision_memo(data: Dict[str, Any]) -> ValidationResult:
    """Basic validation for decision memo"""
    errors = []
    warnings = []
    
    required_keys = ['decision_id', 'timestamp', 'security_id', 'decision_type', 
                     'factual_basis', 'assumptions', 'valuation_analysis', 
                     'qualitative_assessment', 'risk_factors', 'decision_rationale']
    
    for key in required_keys:
        if key not in data:
            errors.append(f"Missing required field: {key}")
    
    if 'decision_type' in data:
        valid_types = ['buy', 'sell', 'hold', 'trim', 'add']
        if data['decision_type'] not in valid_types:
            errors.append(f"Invalid decision_type. Must be one of: {', '.join(valid_types)}")
    
    valid = len(errors) == 0
    return ValidationResult(valid, errors, warnings)


def validate_with_schema(file_path: Path, schema_path: Path) -> ValidationResult:
    """
    Validate JSON file against JSON Schema.
    
    Uses jsonschema library for full Draft-07 validation if available.
    Falls back to basic validation if jsonschema not installed.
    """
    errors = []
    warnings = []
    
    # First check file is valid JSON
    json_result = validate_json_file(file_path)
    if not json_result:
        return json_result
    
    # Load data
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Load schema
    if not schema_path.exists():
        errors.append(f"Schema file not found: {schema_path}")
        return ValidationResult(False, errors, warnings)
    
    try:
        with open(schema_path, 'r') as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"Schema file is not valid JSON: {e}")
        return ValidationResult(False, errors, warnings)
    
    # Perform full JSON Schema validation if available
    if JSONSCHEMA_AVAILABLE:
        try:
            validator = Draft7Validator(schema)
            validation_errors = list(validator.iter_errors(data))
            
            if validation_errors:
                for error in validation_errors:
                    # Format error path
                    path = '.'.join(str(p) for p in error.path) if error.path else 'root'
                    errors.append(f"{path}: {error.message}")
                
                return ValidationResult(False, errors, warnings)
            else:
                return ValidationResult(True, errors, warnings)
        
        except Exception as e:
            errors.append(f"Schema validation error: {e}")
            return ValidationResult(False, errors, warnings)
    
    else:
        # Fallback to basic validation
        warnings.append("jsonschema library not installed - performing basic validation only")
        warnings.append("Install with: pip install jsonschema>=4.17.0")
        
        schema_name = schema_path.name
        
        if 'portfolio-state' in schema_name:
            return validate_portfolio_snapshot(data)
        elif 'valuation-model' in schema_name:
            return validate_valuation_model(data)
        elif 'decision-memo' in schema_name:
            return validate_decision_memo(data)
        else:
            warnings.append(f"Unknown schema type: {schema_name}")
            return ValidationResult(True, errors, warnings)
