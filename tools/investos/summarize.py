"""
Portfolio State Summarizer

Creates deterministic, fact-based summaries of portfolio snapshots.
NO opinions, NO valuations, NO assumptions - just facts.

Output: analysis/state/summary.json
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class SummaryError(Exception):
    """Raised when summary generation fails"""
    pass


def _classify_security_type(name: str, isin: str) -> str:
    """
    Classify security as ETF, stock, or other based on name heuristics.
    Conservative classification - defaults to 'other' when uncertain.
    """
    name_lower = name.lower()
    
    # ETF indicators
    etf_keywords = ['etf', 'ishares', 'vanguard', 'invesco', 'spdr', 'xtrackers']
    if any(kw in name_lower for kw in etf_keywords):
        return 'ETF'
    
    # Known company patterns that are stocks
    # Most individual companies have simple names like "Company Inc."
    # ETCs and funds tend to have complex names
    if any(keyword in name_lower for keyword in ['reg. shares', 'registered shares', 'class', 'inc.', 'corp.', 'ltd.']):
        # But check it's not also an ETF/fund
        if not any(keyword in name_lower for keyword in ['fund', 'trust', 'plc open end', 'metals plc']):
            return 'Stock'
    
    # Default to other (includes gold ETCs, bonds, etc.)
    return 'Other'


def _calculate_concentration_flags(holdings: List[Dict[str, Any]], total_value: float) -> List[Dict[str, Any]]:
    """
    Flag holdings with >10% concentration.
    Returns list of {name, weight_pct, isin}
    """
    flags = []
    
    for holding in holdings:
        market_value = holding.get('market_data', {}).get('market_value')
        if market_value is None or total_value <= 0:
            continue
        
        weight_pct = (market_value / total_value) * 100
        
        if weight_pct > 10.0:
            flags.append({
                'name': holding['name'],
                'isin': holding['isin'],
                'weight_pct': round(weight_pct, 2),
                'market_value': market_value
            })
    
    # Sort by weight descending
    flags.sort(key=lambda x: x['weight_pct'], reverse=True)
    
    return flags


def _load_latest_explanation(repo_root: Path) -> Optional[Dict[str, Any]]:
    """
    Attempt to load the most recent explanation from monitoring/explanations/.
    Returns None if no explanations exist.
    """
    explanations_dir = repo_root / 'monitoring' / 'explanations'
    
    if not explanations_dir.exists():
        return None
    
    # Find all explanation.json files
    explanation_files = list(explanations_dir.rglob('explanation.json'))
    
    if not explanation_files:
        return None
    
    # Get most recent by modification time
    latest_file = max(explanation_files, key=lambda p: p.stat().st_mtime)
    
    try:
        with open(latest_file, 'r') as f:
            return json.load(f)
    except Exception:
        return None


def create_summary(snapshot_path: Path, repo_root: Path) -> Dict[str, Any]:
    """
    Create deterministic portfolio summary from snapshot.
    
    Args:
        snapshot_path: Path to portfolio snapshot JSON
        repo_root: Repository root directory
    
    Returns:
        Summary dictionary with facts only
    
    Raises:
        SummaryError: If summary creation fails
    """
    # Load snapshot
    try:
        with open(snapshot_path, 'r') as f:
            snapshot = json.load(f)
    except Exception as e:
        raise SummaryError(f"Failed to load snapshot: {e}")
    
    # Extract core facts
    holdings = snapshot.get('holdings', [])
    totals = snapshot.get('totals', {})
    base_currency = totals.get('base_currency', 'EUR')
    
    total_value = totals.get('total_portfolio_value', 0)
    total_cash = totals.get('total_cash', 0)
    
    # Calculate holdings with market values
    valued_holdings = []
    for holding in holdings:
        market_value = holding.get('market_data', {}).get('market_value')
        if market_value is not None:
            valued_holdings.append({
                'name': holding['name'],
                'isin': holding['isin'],
                'market_value': market_value,
                'weight_pct': (market_value / total_value * 100) if total_value > 0 else 0,
                'quantity': holding.get('quantity'),
                'currency': holding.get('currency'),
                'type': _classify_security_type(holding['name'], holding['isin'])
            })
    
    # Sort by market value descending
    valued_holdings.sort(key=lambda x: x['market_value'], reverse=True)
    
    # Top 5 holdings
    top_5 = valued_holdings[:5]
    
    # Security type breakdown
    type_breakdown = {}
    for holding in valued_holdings:
        sec_type = holding['type']
        if sec_type not in type_breakdown:
            type_breakdown[sec_type] = {'count': 0, 'market_value': 0}
        type_breakdown[sec_type]['count'] += 1
        type_breakdown[sec_type]['market_value'] += holding['market_value']
    
    # Calculate percentages
    for sec_type in type_breakdown:
        if total_value > 0:
            type_breakdown[sec_type]['weight_pct'] = round(
                (type_breakdown[sec_type]['market_value'] / total_value) * 100, 2
            )
        else:
            type_breakdown[sec_type]['weight_pct'] = 0
    
    # Concentration flags
    concentration_flags = _calculate_concentration_flags(holdings, total_value)
    
    # Recent changes (from explanation if available)
    recent_changes = None
    explanation = _load_latest_explanation(repo_root)
    if explanation:
        recent_changes = {
            'explanation_available': True,
            'from_snapshot': explanation.get('snapshot_A_id'),
            'to_snapshot': explanation.get('snapshot_B_id'),
            'delta_abs': explanation.get('totals', {}).get('delta_abs'),
            'delta_pct': explanation.get('totals', {}).get('delta_pct'),
            'top_drivers': explanation.get('drivers', [])[:5]  # Top 5 drivers
        }
    
    # Build summary
    summary = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'summary_version': '1.0.0',
        'snapshot': {
            'snapshot_id': snapshot.get('snapshot_id'),
            'timestamp': snapshot.get('timestamp'),
            'source_file': snapshot_path.name
        },
        'portfolio_totals': {
            'total_portfolio_value': total_value,
            'total_cash': total_cash,
            'base_currency': base_currency
        },
        'holdings_count': {
            'total': len(holdings),
            'with_market_value': len(valued_holdings)
        },
        'top_holdings': [
            {
                'name': h['name'],
                'isin': h['isin'],
                'market_value': h['market_value'],
                'weight_pct': round(h['weight_pct'], 2),
                'type': h['type']
            }
            for h in top_5
        ],
        'security_type_breakdown': type_breakdown,
        'concentration': {
            'holdings_over_10pct': len(concentration_flags),
            'flags': concentration_flags
        },
        'recent_changes': recent_changes,
        'data_quality': {
            'holdings_without_market_value': len(holdings) - len(valued_holdings),
            'snapshot_validation': 'not_checked'
        }
    }
    
    return summary


def run_summarize(repo_root: Path, config, output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Main entry point for summarize command.
    
    Args:
        repo_root: Repository root
        config: Configuration object
        output_path: Optional custom output path (defaults to analysis/state/summary.json)
    
    Returns:
        Summary dictionary
    
    Raises:
        SummaryError: If summarization fails
    """
    # Find latest snapshot
    snapshots_dir = repo_root / config.snapshots_dir
    
    if not snapshots_dir.exists():
        raise SummaryError(f"Snapshots directory not found: {snapshots_dir}")
    
    # Get all JSON files except latest.json
    snapshot_files = sorted([
        p for p in snapshots_dir.glob('*.json')
        if p.name != 'latest.json'
    ])
    
    if not snapshot_files:
        raise SummaryError("No portfolio snapshots found")
    
    # Use most recent
    latest_snapshot = snapshot_files[-1]
    
    # Create summary
    summary = create_summary(latest_snapshot, repo_root)
    
    # Write to output
    if output_path is None:
        output_path = repo_root / 'analysis' / 'state' / 'summary.json'
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Also write latest.json pointer
    latest_pointer = {
        'latest_snapshot': latest_snapshot.name,
        'latest_summary': 'summary.json',
        'updated_at': datetime.utcnow().isoformat() + 'Z'
    }
    
    latest_path = repo_root / 'analysis' / 'state' / 'latest.json'
    with open(latest_path, 'w') as f:
        json.dump(latest_pointer, f, indent=2)
    
    return summary
