"""
Valuation v1 Engine for Investment OS

Deterministic valuation pipeline that:
- Reads portfolio snapshots
- Classifies securities by type
- Produces schema-compliant valuation outputs
- NO external API calls or data fetching
- Clear separation of facts, assumptions, and derived values

Conservative approach:
- Missing data => incomplete status + warnings
- No guessing or estimation
- Explicit assumption documentation
"""

import json
import yaml
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple


class ValuationError(Exception):
    """Error during valuation processing"""
    pass


def classify_security_type(holding: Dict[str, Any]) -> str:
    """
    Classify security type using deterministic rules based on name/ISIN.
    
    Rules:
    - ETF indicators in name => "etf"
    - Physical commodity ETP => "commodity_etp"
    - Default => "stock"
    
    NO external data fetching.
    
    Args:
        holding: Holding dict from portfolio snapshot
    
    Returns:
        security_type: "etf" | "commodity_etp" | "stock"
    """
    name = holding.get('name', '').upper()
    isin = holding.get('isin', '')
    
    # ETF indicators
    etf_indicators = ['ETF', 'UCITS', 'INDEX', 'ISHARES', 'VANGUARD', 'INVESCO']
    if any(indicator in name for indicator in etf_indicators):
        return 'etf'
    
    # Commodity ETP (Irish domiciled physical commodity products)
    if isin.startswith('IE') and ('PHYSICAL' in name or 'GOLD' in name or 'SILVER' in name):
        return 'commodity_etp'
    
    # Default to stock
    return 'stock'


def load_assumptions(assumptions_path: Path, profile: str = 'conservative') -> Dict[str, Any]:
    """
    Load valuation assumptions from YAML file.
    
    Args:
        assumptions_path: Path to assumptions YAML file
        profile: Assumption profile name (conservative | base_case | optimistic)
    
    Returns:
        Dict of assumptions
    
    Raises:
        ValuationError: If assumptions file not found or invalid
    """
    if not assumptions_path.exists():
        raise ValuationError(f"Assumptions file not found: {assumptions_path}")
    
    try:
        with open(assumptions_path, 'r') as f:
            assumptions = yaml.safe_load(f)
        
        if not assumptions:
            raise ValuationError("Assumptions file is empty")
        
        # Extract profile-specific overrides if present
        if 'assumption_profiles' in assumptions and profile in assumptions['assumption_profiles']:
            # TODO: Apply profile-specific adjustments
            pass
        
        return assumptions
    
    except yaml.YAMLError as e:
        raise ValuationError(f"Invalid YAML in assumptions file: {e}")
    except IOError as e:
        raise ValuationError(f"Cannot read assumptions file: {e}")


def load_fundamentals_input(isin: str, inputs_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Load user-provided fundamentals input for a security.
    
    Args:
        isin: Security ISIN
        inputs_dir: Directory containing input files (valuations/inputs/)
    
    Returns:
        Dict of fundamental inputs if file exists, None otherwise
    """
    input_file = inputs_dir / f"{isin}.json"
    
    if not input_file.exists():
        return None
    
    try:
        with open(input_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        # Log warning but don't fail - return None
        print(f"Warning: Could not load input file for {isin}: {e}")
        return None


def create_valuation_scaffold(holding: Dict[str, Any], output_path: Path):
    """
    Create a scaffold input file for a security missing fundamentals.
    
    Does NOT overwrite existing files.
    
    Args:
        holding: Holding dict from snapshot
        output_path: Path where scaffold should be written
    """
    if output_path.exists():
        return  # Never overwrite existing input files
    
    isin = holding.get('isin', 'UNKNOWN')
    name = holding.get('name', 'Unknown Security')
    
    scaffold = {
        "_comment": "Manual input file for fundamental data - fill in TODO sections",
        "security_id": isin,
        "security_name": name,
        "data_as_of_date": "TODO: YYYY-MM-DD",
        "currency": holding.get('currency', 'EUR'),
        
        "fundamentals": {
            "revenue": {
                "current_ttm": "TODO: number",
                "historical_5y": "TODO: [year, revenue] pairs",
                "comment": "Trailing twelve months revenue and 5-year history"
            },
            "earnings": {
                "net_income_ttm": "TODO: number",
                "historical_5y": "TODO: [year, net_income] pairs",
                "comment": "Net income (earnings) trailing twelve months"
            },
            "cash_flow": {
                "fcf_ttm": "TODO: number",
                "historical_5y": "TODO: [year, fcf] pairs",
                "comment": "Free cash flow = Operating CF - CapEx"
            },
            "balance_sheet": {
                "total_debt": "TODO: number",
                "cash_and_equivalents": "TODO: number",
                "shareholders_equity": "TODO: number",
                "shares_outstanding": "TODO: number"
            },
            "margins": {
                "operating_margin": "TODO: decimal (e.g., 0.25 = 25%)",
                "net_margin": "TODO: decimal",
                "comment": "Use trailing 5-year average or current if declining"
            }
        },
        
        "sources": {
            "data_provider": "TODO: Annual report, Bloomberg, etc.",
            "links": [
                "TODO: Add source URLs"
            ],
            "notes": "TODO: Add any notes about data quality or adjustments"
        }
    }
    
    # Create directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(scaffold, f, indent=2)


def value_stock(
    holding: Dict[str, Any],
    snapshot: Dict[str, Any],
    assumptions: Dict[str, Any],
    fundamentals: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Value a stock using fundamentals or mark as incomplete.
    
    Args:
        holding: Holding dict from snapshot
        snapshot: Full snapshot for context
        assumptions: Valuation assumptions
        fundamentals: User-provided fundamentals (or None if missing)
    
    Returns:
        Valuation dict conforming to schema
    """
    isin = holding.get('isin', 'UNKNOWN')
    name = holding.get('name', 'Unknown')
    now = datetime.now(timezone.utc)
    
    valuation_id = f"{isin}-valuation-{now.strftime('%Y-%m-%d')}"
    
    # Base valuation structure
    valuation = {
        'valuation_id': valuation_id,
        'timestamp': now.isoformat(),
        'version': '1.0.0',
        'security_id': isin,
        'security_name': name,
        'snapshot_reference': {
            'snapshot_id': snapshot.get('snapshot_id'),
            'snapshot_timestamp': snapshot.get('timestamp')
        },
        'facts': {
            'market_value': holding.get('market_data', {}).get('market_value') if holding.get('market_data') else None,
            'quantity': holding.get('quantity'),
            'currency': holding.get('currency', 'EUR'),
            'price': None  # Not available in current snapshot format
        },
        'warnings': [],
        'links': {
            'inputs_file': f"valuations/inputs/{isin}.json",
            'dossier': f"research/dossiers/{isin}.md",
            'decision_memos': f"decisions/memos/{isin}/"
        }
    }
    
    # If no fundamentals, mark as incomplete
    if not fundamentals:
        valuation['status'] = 'incomplete'
        valuation['methodology'] = 'incomplete_missing_inputs'
        valuation['warnings'].append(f"Missing fundamentals input file: valuations/inputs/{isin}.json")
        valuation['warnings'].append("Run with --emit-scaffolds to create input template")
        
        # Minimal assumptions structure
        valuation['assumptions'] = {
            'assumption_set': assumptions.get('assumption_set_name', 'conservative'),
            'revenue_growth': {},
            'margin_assumptions': {},
            'discount_rate': {
                'rate': assumptions.get('discount_rate', {}).get('total_rate', 0.12),
                'components': {}
            }
        }
        
        # No valuation computed
        valuation['valuation'] = {
            'intrinsic_value': None,
            'intrinsic_value_range': {
                'low': None,
                'base': None,
                'high': None
            },
            'current_price': valuation['facts']['market_value'] / valuation['facts']['quantity'] if valuation['facts']['quantity'] and valuation['facts']['market_value'] else None,
            'implied_upside': None,
            'margin_of_safety_met': None
        }
        
        return valuation
    
    # TODO: If fundamentals exist, implement full valuation
    # For v1, we still mark as incomplete but acknowledge inputs exist
    valuation['status'] = 'incomplete'
    valuation['methodology'] = 'multiple_band'  # Or 'dcf' based on inputs
    valuation['warnings'].append("Full DCF valuation not yet implemented in v1")
    valuation['warnings'].append("Input file exists but valuation computation pending")
    
    # Extract assumptions from YAML
    discount_rate_config = assumptions.get('discount_rate', {})
    margin_of_safety_config = assumptions.get('margin_of_safety', {})
    
    valuation['assumptions'] = {
        'assumption_set': assumptions.get('assumption_set_name', 'conservative'),
        'revenue_growth': {
            'short_term_rate': assumptions.get('revenue_growth', {}).get('short_term_rate', 0.07),
            'long_term_rate': assumptions.get('revenue_growth', {}).get('long_term_rate', 0.03),
            'rationale': assumptions.get('revenue_growth', {}).get('rationale', 'Conservative growth assumptions'),
            'sources': []
        },
        'margin_assumptions': {
            'operating_margin': fundamentals.get('fundamentals', {}).get('margins', {}).get('operating_margin') if isinstance(fundamentals.get('fundamentals', {}).get('margins', {}).get('operating_margin'), (int, float)) else None,
            'net_margin': fundamentals.get('fundamentals', {}).get('margins', {}).get('net_margin') if isinstance(fundamentals.get('fundamentals', {}).get('margins', {}).get('net_margin'), (int, float)) else None,
            'rationale': 'Based on historical margins from input file'
        },
        'discount_rate': {
            'rate': discount_rate_config.get('total_rate', 0.12),
            'components': {
                'risk_free_rate': discount_rate_config.get('components', {}).get('risk_free_rate', 0.04),
                'equity_risk_premium': discount_rate_config.get('components', {}).get('equity_risk_premium', 0.05),
                'company_specific_risk': discount_rate_config.get('components', {}).get('company_specific_risk', 0.03)
            },
            'rationale': discount_rate_config.get('rationale', 'Conservative required return')
        },
        'margin_of_safety': {
            'required': margin_of_safety_config.get('default_required', 0.25),
            'rationale': margin_of_safety_config.get('rationale', 'Standard margin of safety for conservatism')
        }
    }
    
    # Placeholder valuation (not computed in v1)
    valuation['valuation'] = {
        'intrinsic_value': None,
        'intrinsic_value_range': {
            'low': None,
            'base': None,
            'high': None
        },
        'current_price': valuation['facts']['market_value'] / valuation['facts']['quantity'] if valuation['facts']['quantity'] and valuation['facts']['market_value'] else None,
        'implied_upside': None,
        'margin_of_safety_met': None,
        'comment': 'Full valuation computation pending - v1 scaffolding only'
    }
    
    return valuation


def value_etf_or_commodity(
    holding: Dict[str, Any],
    snapshot: Dict[str, Any],
    assumptions: Dict[str, Any],
    security_type: str
) -> Dict[str, Any]:
    """
    Value an ETF or commodity ETP as allocation vehicle.
    
    No intrinsic value computed - these are allocation tools, not individual businesses.
    
    Args:
        holding: Holding dict from snapshot
        snapshot: Full snapshot for context
        assumptions: Valuation assumptions
        security_type: "etf" or "commodity_etp"
    
    Returns:
        Valuation dict conforming to schema
    """
    isin = holding.get('isin', 'UNKNOWN')
    name = holding.get('name', 'Unknown')
    now = datetime.now(timezone.utc)
    
    valuation_id = f"{isin}-valuation-{now.strftime('%Y-%m-%d')}"
    
    valuation = {
        'valuation_id': valuation_id,
        'timestamp': now.isoformat(),
        'version': '1.0.0',
        'security_id': isin,
        'security_name': name,
        'security_type': security_type,
        'snapshot_reference': {
            'snapshot_id': snapshot.get('snapshot_id'),
            'snapshot_timestamp': snapshot.get('timestamp')
        },
        'status': 'complete',
        'methodology': 'allocation_vehicle_no_intrinsic',
        'facts': {
            'market_value': holding.get('market_data', {}).get('market_value') if holding.get('market_data') else None,
            'quantity': holding.get('quantity'),
            'currency': holding.get('currency', 'EUR'),
            'price': None
        },
        'assumptions': {
            'assumption_set': assumptions.get('assumption_set_name', 'conservative'),
            'allocation_rationale': f"{security_type.upper()} - allocation vehicle, not valued for intrinsic value",
            'expected_return_range': None,  # Could be added from assumptions if defined
            'risk_notes': 'ETF/ETP holdings - diversification and allocation purpose',
            'revenue_growth': {},  # Not applicable
            'margin_assumptions': {},  # Not applicable
            'discount_rate': {
                'rate': None,
                'components': {},
                'rationale': 'Not applicable for allocation vehicles'
            }
        },
        'valuation': {
            'intrinsic_value': None,
            'intrinsic_value_range': {
                'low': None,
                'base': None,
                'high': None
            },
            'current_price': holding.get('market_data', {}).get('market_value', 0) / holding.get('quantity', 1) if holding.get('quantity') and holding.get('quantity') > 0 else None,
            'implied_upside': None,
            'margin_of_safety_met': None,
            'comment': f'Allocation vehicle - no intrinsic value calculated. Used for {security_type} exposure.'
        },
        'warnings': [],
        'links': {
            'inputs_file': None,  # Not applicable
            'dossier': f"research/dossiers/{isin}.md",
            'decision_memos': f"decisions/memos/{isin}/"
        }
    }
    
    return valuation


def create_portfolio_summary(
    snapshot: Dict[str, Any],
    valuations: List[Dict[str, Any]],
    output_dir: Path
) -> Dict[str, Any]:
    """
    Create portfolio-level valuation summary.
    
    Args:
        snapshot: Portfolio snapshot
        valuations: List of all holding valuations
        output_dir: Output directory
    
    Returns:
        Portfolio summary dict
    """
    now = datetime.now(timezone.utc)
    
    # Calculate position weights
    total_portfolio_value = snapshot.get('totals', {}).get('total_portfolio_value', 0)
    
    position_sizing = []
    for val in valuations:
        market_value = val.get('facts', {}).get('market_value', 0) or 0
        weight_pct = (market_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
        
        position_sizing.append({
            'isin': val.get('security_id'),
            'name': val.get('security_name'),
            'market_value': market_value,
            'weight_pct': round(weight_pct, 2)
        })
    
    # Sort by weight descending
    position_sizing.sort(key=lambda x: x['weight_pct'], reverse=True)
    
    # Count by status
    complete_count = sum(1 for v in valuations if v.get('status') == 'complete')
    incomplete_count = sum(1 for v in valuations if v.get('status') == 'incomplete')
    allocation_vehicle_count = sum(1 for v in valuations if v.get('methodology') == 'allocation_vehicle_no_intrinsic')
    
    # Collect all warnings
    all_warnings = []
    for val in valuations:
        for warning in val.get('warnings', []):
            all_warnings.append(f"{val.get('security_id')}: {warning}")
    
    summary = {
        'summary_id': f"portfolio-summary-{now.strftime('%Y-%m-%d-%H%M%S')}",
        'timestamp': now.isoformat(),
        'snapshot_reference': {
            'snapshot_id': snapshot.get('snapshot_id'),
            'snapshot_timestamp': snapshot.get('timestamp')
        },
        'portfolio_metrics': {
            'total_market_value': snapshot.get('totals', {}).get('total_market_value', 0),
            'total_cash': snapshot.get('totals', {}).get('total_cash', 0),
            'total_portfolio_value': total_portfolio_value,
            'base_currency': snapshot.get('totals', {}).get('base_currency', 'EUR'),
            'holdings_count': len(valuations)
        },
        'position_sizing': position_sizing,
        'valuation_status': {
            'complete': complete_count,
            'incomplete': incomplete_count,
            'allocation_vehicles': allocation_vehicle_count
        },
        'top_holdings': position_sizing[:5],  # Top 5 by weight
        'concentration_risks': [
            pos for pos in position_sizing if pos['weight_pct'] >= 10.0
        ],
        'warnings': all_warnings,
        'output_location': str(output_dir)
    }
    
    return summary


def run_valuation(
    snapshot_path: Path,
    assumptions_path: Path,
    output_dir: Path,
    profile: str = 'conservative',
    only_isin: Optional[str] = None,
    emit_scaffolds: bool = False
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Run valuation pipeline on a portfolio snapshot.
    
    Args:
        snapshot_path: Path to portfolio snapshot JSON
        assumptions_path: Path to assumptions YAML
        output_dir: Output directory for valuations
        profile: Assumption profile name
        only_isin: If set, only value this ISIN
        emit_scaffolds: If True, create input scaffolds for missing fundamentals
    
    Returns:
        Tuple of (valuations_list, portfolio_summary)
    
    Raises:
        ValuationError: If critical error occurs
    """
    # Load snapshot
    if not snapshot_path.exists():
        raise ValuationError(f"Snapshot not found: {snapshot_path}")
    
    with open(snapshot_path, 'r') as f:
        snapshot = json.load(f)
    
    # Load assumptions
    assumptions = load_assumptions(assumptions_path, profile)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Inputs directory for fundamentals
    repo_root = snapshot_path.parent.parent  # Assuming snapshot in portfolio/snapshots/
    inputs_dir = repo_root / 'valuations' / 'inputs'
    
    valuations = []
    
    holdings = snapshot.get('holdings', [])
    
    if only_isin:
        holdings = [h for h in holdings if h.get('isin') == only_isin]
        if not holdings:
            raise ValuationError(f"No holding found with ISIN: {only_isin}")
    
    for holding in holdings:
        isin = holding.get('isin', 'UNKNOWN')
        
        # Classify security type
        security_type = classify_security_type(holding)
        
        # Value based on type
        if security_type == 'stock':
            # Load fundamentals if available
            fundamentals = load_fundamentals_input(isin, inputs_dir)
            
            # Create scaffold if requested and missing
            if emit_scaffolds and not fundamentals:
                scaffold_path = inputs_dir / f"{isin}.json"
                create_valuation_scaffold(holding, scaffold_path)
                print(f"Created input scaffold: {scaffold_path}")
            
            valuation = value_stock(holding, snapshot, assumptions, fundamentals)
        
        else:  # ETF or commodity ETP
            valuation = value_etf_or_commodity(holding, snapshot, assumptions, security_type)
        
        valuations.append(valuation)
        
        # Write individual valuation file
        val_file = output_dir / f"{isin}-valuation.json"
        with open(val_file, 'w') as f:
            json.dump(valuation, f, indent=2)
    
    # Create portfolio summary
    summary = create_portfolio_summary(snapshot, valuations, output_dir)
    
    # Write summary
    summary_file = output_dir / 'portfolio_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    return valuations, summary
