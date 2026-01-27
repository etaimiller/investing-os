"""
Portfolio Change Explanation Engine

Deterministic, offline attribution of portfolio changes between two snapshots.
Answers: "What mechanically drove the change?"

NO external APIs, NO price fetching, NO news analysis.
Pure mechanical attribution from snapshot data.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional


class ExplainError(Exception):
    """Error during explanation processing"""
    pass


def build_holding_key(holding: Dict[str, Any], index: int, warnings: List[str]) -> str:
    """
    Build stable holding key for matching across snapshots.
    
    Key format: account_id::isin
    Fallback: account_id::security_id
    Last resort: unknown::<index>
    
    Args:
        holding: Holding dict from snapshot
        index: Holding index (for fallback)
        warnings: Warning list to append to
    
    Returns:
        Stable key string
    """
    account_id = holding.get('account_id', 'unknown')
    isin = holding.get('isin')
    
    if isin:
        return f"{account_id}::{isin}"
    
    security_id = holding.get('security_id')
    if security_id:
        warnings.append(f"Holding missing ISIN, using security_id: {security_id}")
        return f"{account_id}::{security_id}"
    
    warnings.append(f"Holding {index} missing both ISIN and security_id - using index-based key")
    return f"{account_id}::unknown::{index}"


def extract_market_value(holding: Dict[str, Any]) -> Optional[float]:
    """
    Extract market value from holding.
    
    Returns None if not present (will trigger warning elsewhere).
    """
    market_data = holding.get('market_data', {})
    if not market_data:
        return None
    
    return market_data.get('market_value')


def compute_portfolio_total(snapshot: Dict[str, Any], warnings: List[str]) -> Tuple[float, str]:
    """
    Compute portfolio total value.
    
    Prefers snapshot.totals.total_portfolio_value if consistent.
    Otherwise recomputes from holdings + cash.
    
    Returns:
        (total_value, source)
        source is "from_snapshot" or "recomputed"
    """
    # Try snapshot totals first
    totals = snapshot.get('totals', {})
    snapshot_total = totals.get('total_portfolio_value')
    
    # Compute from holdings + cash
    holdings_total = 0.0
    holdings = snapshot.get('holdings', [])
    for holding in holdings:
        mv = extract_market_value(holding)
        if mv is not None:
            holdings_total += mv
    
    cash_total = 0.0
    cash_list = snapshot.get('cash', [])
    for cash_item in cash_list:
        amount = cash_item.get('amount', 0)
        cash_total += amount
    
    computed_total = holdings_total + cash_total
    
    # Check consistency
    if snapshot_total is not None:
        # Allow small floating point differences
        if abs(snapshot_total - computed_total) < 0.01:
            return snapshot_total, "from_snapshot"
        else:
            warnings.append(
                f"Snapshot total ({snapshot_total:.2f}) differs from computed "
                f"({computed_total:.2f}) - using computed value"
            )
            return computed_total, "recomputed"
    else:
        return computed_total, "recomputed"


def classify_driver(
    key: str,
    holding_A: Optional[Dict[str, Any]],
    holding_B: Optional[Dict[str, Any]],
    warnings: List[str]
) -> Dict[str, Any]:
    """
    Classify a single holding change into driver type.
    
    Logic:
    - Only in B -> new_position
    - Only in A -> position_removed
    - Both, quantity unchanged, mv changed -> price_change
    - Both, quantity changed -> quantity_change
    
    Returns:
        Driver dict with type, contribution, and details
    """
    # Extract account_id, isin from key
    parts = key.split('::', 1)
    account_id = parts[0]
    identifier = parts[1] if len(parts) > 1 else ''
    
    # New position
    if holding_A is None and holding_B is not None:
        mv_B = extract_market_value(holding_B)
        if mv_B is None:
            warnings.append(f"New position {identifier} missing market_value")
            mv_B = 0.0
        
        return {
            'type': 'new_position',
            'account_id': account_id,
            'isin': holding_B.get('isin'),
            'name': holding_B.get('name'),
            'contribution_abs': mv_B,
            'details': {
                'mv_B': mv_B,
                'notes': 'New position opened'
            }
        }
    
    # Position removed
    if holding_A is not None and holding_B is None:
        mv_A = extract_market_value(holding_A)
        if mv_A is None:
            warnings.append(f"Removed position {identifier} missing market_value")
            mv_A = 0.0
        
        return {
            'type': 'position_removed',
            'account_id': account_id,
            'isin': holding_A.get('isin'),
            'name': holding_A.get('name'),
            'contribution_abs': -mv_A,
            'details': {
                'mv_A': mv_A,
                'notes': 'Position closed'
            }
        }
    
    # Position in both snapshots
    quantity_A = holding_A.get('quantity')
    quantity_B = holding_B.get('quantity')
    mv_A = extract_market_value(holding_A)
    mv_B = extract_market_value(holding_B)
    
    # Check for missing data
    if mv_A is None or mv_B is None:
        warnings.append(f"Holding {identifier} missing market_value in one or both snapshots")
        mv_A = mv_A or 0.0
        mv_B = mv_B or 0.0
    
    contribution = mv_B - mv_A
    
    # Classify based on quantity change
    if quantity_A is not None and quantity_B is not None:
        quantity_delta = quantity_B - quantity_A
        
        if abs(quantity_delta) < 0.0001:  # Unchanged quantity
            return {
                'type': 'price_change',
                'account_id': account_id,
                'isin': holding_A.get('isin') or holding_B.get('isin'),
                'name': holding_A.get('name') or holding_B.get('name'),
                'contribution_abs': contribution,
                'details': {
                    'quantity_A': quantity_A,
                    'quantity_B': quantity_B,
                    'mv_A': mv_A,
                    'mv_B': mv_B,
                    'notes': 'Quantity unchanged, value changed (price effect)'
                }
            }
        else:
            return {
                'type': 'quantity_change',
                'account_id': account_id,
                'isin': holding_A.get('isin') or holding_B.get('isin'),
                'name': holding_A.get('name') or holding_B.get('name'),
                'contribution_abs': contribution,
                'details': {
                    'quantity_A': quantity_A,
                    'quantity_B': quantity_B,
                    'quantity_delta': quantity_delta,
                    'mv_A': mv_A,
                    'mv_B': mv_B,
                    'notes': f'Quantity changed by {quantity_delta:+.4f} shares'
                }
            }
    else:
        # Missing quantity data - classify as price_change by default
        warnings.append(f"Holding {identifier} missing quantity in one or both snapshots")
        return {
            'type': 'price_change',
            'account_id': account_id,
            'isin': holding_A.get('isin') or holding_B.get('isin'),
            'name': holding_A.get('name') or holding_B.get('name'),
            'contribution_abs': contribution,
            'details': {
                'quantity_A': quantity_A,
                'quantity_B': quantity_B,
                'mv_A': mv_A,
                'mv_B': mv_B,
                'notes': 'Missing quantity data - classified as price effect'
            }
        }


def compute_cash_changes(snapshot_A: Dict[str, Any], snapshot_B: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Compute cash balance changes between snapshots.
    
    Returns list of cash_change drivers.
    """
    cash_A_map = {}
    cash_B_map = {}
    
    # Build maps: (account_id, currency) -> amount
    for cash_item in snapshot_A.get('cash', []):
        key = (cash_item.get('account_id', 'unknown'), cash_item.get('currency', 'UNKNOWN'))
        cash_A_map[key] = cash_item.get('amount', 0.0)
    
    for cash_item in snapshot_B.get('cash', []):
        key = (cash_item.get('account_id', 'unknown'), cash_item.get('currency', 'UNKNOWN'))
        cash_B_map[key] = cash_item.get('amount', 0.0)
    
    # Find all unique keys
    all_keys = set(cash_A_map.keys()) | set(cash_B_map.keys())
    
    drivers = []
    for key in all_keys:
        account_id, currency = key
        amount_A = cash_A_map.get(key, 0.0)
        amount_B = cash_B_map.get(key, 0.0)
        delta = amount_B - amount_A
        
        if abs(delta) > 0.01:  # Ignore tiny differences
            drivers.append({
                'type': 'cash_change',
                'account_id': account_id,
                'currency': currency,
                'contribution_abs': delta,
                'details': {
                    'amount_A': amount_A,
                    'amount_B': amount_B,
                    'delta': delta,
                    'notes': f'Cash {"increased" if delta > 0 else "decreased"} by {abs(delta):.2f} {currency}'
                }
            })
    
    return drivers


def run_explanation(
    snapshot_A_path: Path,
    snapshot_B_path: Path,
    output_dir: Path,
    format_type: str = 'json',
    strict: bool = False
) -> Dict[str, Any]:
    """
    Run portfolio change explanation between two snapshots.
    
    Args:
        snapshot_A_path: Path to "from" snapshot
        snapshot_B_path: Path to "to" snapshot
        output_dir: Output directory for reports
        format_type: Output format ('json', 'md', 'both')
        strict: If True, fail on missing market_value
    
    Returns:
        Report dict
    
    Raises:
        ExplainError: If validation fails or critical errors occur
    """
    warnings = []
    
    # Load snapshots
    if not snapshot_A_path.exists():
        raise ExplainError(f"Snapshot A not found: {snapshot_A_path}")
    if not snapshot_B_path.exists():
        raise ExplainError(f"Snapshot B not found: {snapshot_B_path}")
    
    with open(snapshot_A_path, 'r') as f:
        snapshot_A = json.load(f)
    
    with open(snapshot_B_path, 'r') as f:
        snapshot_B = json.load(f)
    
    # Build holding maps
    holdings_A_map = {}
    for idx, holding in enumerate(snapshot_A.get('holdings', [])):
        key = build_holding_key(holding, idx, warnings)
        holdings_A_map[key] = holding
    
    holdings_B_map = {}
    for idx, holding in enumerate(snapshot_B.get('holdings', [])):
        key = build_holding_key(holding, idx, warnings)
        holdings_B_map[key] = holding
    
    # Compute totals
    total_A, source_A = compute_portfolio_total(snapshot_A, warnings)
    total_B, source_B = compute_portfolio_total(snapshot_B, warnings)
    portfolio_delta = total_B - total_A
    
    # Diff holdings
    all_keys = set(holdings_A_map.keys()) | set(holdings_B_map.keys())
    matched_keys = set(holdings_A_map.keys()) & set(holdings_B_map.keys())
    added_keys = set(holdings_B_map.keys()) - set(holdings_A_map.keys())
    removed_keys = set(holdings_A_map.keys()) - set(holdings_B_map.keys())
    
    # Build drivers
    drivers = []
    missing_mv_count = 0
    
    for key in all_keys:
        holding_A = holdings_A_map.get(key)
        holding_B = holdings_B_map.get(key)
        
        driver = classify_driver(key, holding_A, holding_B, warnings)
        
        # Check for missing market values
        if driver['details'].get('mv_A') == 0.0 or driver['details'].get('mv_B') == 0.0:
            missing_mv_count += 1
            if strict:
                raise ExplainError(f"Strict mode: missing market_value for {key}")
        
        drivers.append(driver)
    
    # Add cash changes
    cash_drivers = compute_cash_changes(snapshot_A, snapshot_B)
    drivers.extend(cash_drivers)
    
    # Compute residual
    explained_sum = sum(d['contribution_abs'] for d in drivers)
    residual = portfolio_delta - explained_sum
    
    # Check residual magnitude
    if abs(portfolio_delta) > 0.01:
        residual_pct = abs(residual) / abs(portfolio_delta)
        if residual_pct > 0.005:  # 0.5%
            warnings.append(
                f"Large unexplained residual: {residual:.2f} "
                f"({residual_pct*100:.2f}% of total delta)"
            )
    
    drivers.append({
        'type': 'residual_unexplained',
        'contribution_abs': residual,
        'details': {
            'explained_sum': explained_sum,
            'portfolio_delta': portfolio_delta,
            'notes': 'Unexplained residual (rounding, fees, timing, etc.)'
        }
    })
    
    # Add contribution percentages
    for driver in drivers:
        if abs(portfolio_delta) > 0.01:
            driver['contribution_pct_of_portfolio_delta'] = (
                driver['contribution_abs'] / portfolio_delta
            )
        else:
            driver['contribution_pct_of_portfolio_delta'] = None
    
    # Sort by absolute contribution (descending)
    drivers.sort(key=lambda d: abs(d['contribution_abs']), reverse=True)
    
    # Build report
    now = datetime.now(timezone.utc)
    report_id = f"explanation-{now.strftime('%Y%m%d-%H%M%S')}"
    
    base_currency = snapshot_B.get('totals', {}).get('base_currency', 'EUR')
    
    report = {
        'report_id': report_id,
        'generated_at': now.isoformat(),
        'from_snapshot': {
            'path': str(snapshot_A_path),
            'snapshot_id': snapshot_A.get('snapshot_id'),
            'timestamp': snapshot_A.get('timestamp')
        },
        'to_snapshot': {
            'path': str(snapshot_B_path),
            'snapshot_id': snapshot_B.get('snapshot_id'),
            'timestamp': snapshot_B.get('timestamp')
        },
        'totals': {
            'from_total': total_A,
            'to_total': total_B,
            'delta_abs': portfolio_delta,
            'delta_pct': (portfolio_delta / total_A) if total_A > 0 else None,
            'base_currency': base_currency,
            'totals_source': source_B  # Use source from "to" snapshot
        },
        'drivers': drivers,
        'warnings': warnings,
        'stats': {
            'holdings_A': len(holdings_A_map),
            'holdings_B': len(holdings_B_map),
            'matched': len(matched_keys),
            'added': len(added_keys),
            'removed': len(removed_keys),
            'missing_market_values_count': missing_mv_count
        }
    }
    
    # Write output
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if format_type in ('json', 'both'):
        json_file = output_dir / 'explanation.json'
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)
    
    if format_type in ('md', 'both'):
        md_file = output_dir / 'explanation.md'
        with open(md_file, 'w') as f:
            f.write(generate_markdown_summary(report))
    
    return report


def generate_markdown_summary(report: Dict[str, Any]) -> str:
    """Generate human-readable markdown summary."""
    lines = []
    
    lines.append(f"# Portfolio Change Explanation\n")
    lines.append(f"**Generated**: {report['generated_at']}\n")
    lines.append(f"**Report ID**: {report['report_id']}\n\n")
    
    # Snapshots
    lines.append("## Snapshots\n")
    lines.append(f"- **From**: {report['from_snapshot']['snapshot_id']} ({report['from_snapshot']['timestamp']})")
    lines.append(f"- **To**: {report['to_snapshot']['snapshot_id']} ({report['to_snapshot']['timestamp']})\n")
    
    # Totals
    totals = report['totals']
    lines.append("## Portfolio Change\n")
    lines.append(f"- **From Total**: {totals['from_total']:,.2f} {totals['base_currency']}")
    lines.append(f"- **To Total**: {totals['to_total']:,.2f} {totals['base_currency']}")
    lines.append(f"- **Change**: {totals['delta_abs']:+,.2f} {totals['base_currency']}")
    if totals['delta_pct'] is not None:
        lines.append(f"- **Change %**: {totals['delta_pct']*100:+.2f}%\n")
    
    # Top drivers
    lines.append("## Top Drivers\n")
    lines.append("| Type | Name | Contribution | % of Change |")
    lines.append("|------|------|--------------|-------------|")
    
    for driver in report['drivers'][:10]:  # Top 10
        name = driver.get('name', driver.get('currency', driver.get('type')))
        contrib = driver['contribution_abs']
        pct = driver.get('contribution_pct_of_portfolio_delta')
        pct_str = f"{pct*100:+.1f}%" if pct is not None else "N/A"
        
        lines.append(f"| {driver['type']} | {name} | {contrib:+,.2f} | {pct_str} |")
    
    # Warnings
    if report['warnings']:
        lines.append("\n## Warnings\n")
        for warning in report['warnings']:
            lines.append(f"- ⚠️  {warning}")
    
    # Stats
    stats = report['stats']
    lines.append("\n## Statistics\n")
    lines.append(f"- Holdings in A: {stats['holdings_A']}")
    lines.append(f"- Holdings in B: {stats['holdings_B']}")
    lines.append(f"- Matched: {stats['matched']}")
    lines.append(f"- Added: {stats['added']}")
    lines.append(f"- Removed: {stats['removed']}")
    
    return '\n'.join(lines)
