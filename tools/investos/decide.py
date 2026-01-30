"""
Decision Memo Generator

Creates structured, auditable decision memos for portfolio actions.
Uses existing portfolio state (Step 7) and investor lenses to frame thinking.

NO recommendations, NO predictions, NO external data.
Only structured reasoning grounded in portfolio facts.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple


class DecideError(Exception):
    """Raised when decision memo generation fails"""
    pass


VALID_ACTIONS = ['new', 'add', 'trim', 'exit', 'hold']


def _slugify(text: str) -> str:
    """Convert text to filename-safe slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '_', text)
    return text[:50]


def _load_summary(repo_root: Path) -> Optional[Dict[str, Any]]:
    """Load portfolio summary if available"""
    summary_path = repo_root / 'analysis' / 'state' / 'summary.json'
    
    if not summary_path.exists():
        return None
    
    try:
        with open(summary_path, 'r') as f:
            return json.load(f)
    except Exception:
        return None


def _load_snapshot(snapshot_path: Path) -> Dict[str, Any]:
    """Load portfolio snapshot"""
    try:
        with open(snapshot_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise DecideError(f"Failed to load snapshot: {e}")


def _find_holding_in_snapshot(snapshot: Dict[str, Any], isin: str) -> Optional[Dict[str, Any]]:
    """Find holding by ISIN in snapshot"""
    for holding in snapshot.get('holdings', []):
        if holding.get('isin') == isin:
            return holding
    return None


def _extract_portfolio_context(
    isin: Optional[str],
    action: str,
    snapshot: Dict[str, Any],
    summary: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Extract portfolio context for decision framing"""
    context = {
        'total_value': snapshot.get('totals', {}).get('total_portfolio_value', 0),
        'base_currency': snapshot.get('totals', {}).get('base_currency', 'EUR'),
        'holdings_count': len(snapshot.get('holdings', [])),
        'snapshot_id': snapshot.get('snapshot_id', 'unknown'),
        'snapshot_date': snapshot.get('timestamp', 'unknown')
    }
    
    # If ISIN provided, find current position
    if isin:
        holding = _find_holding_in_snapshot(snapshot, isin)
        if holding:
            market_value = holding.get('market_data', {}).get('market_value', 0)
            if context['total_value'] > 0:
                weight_pct = (market_value / context['total_value']) * 100
            else:
                weight_pct = 0
            
            context['current_holding'] = {
                'name': holding.get('name', 'Unknown'),
                'isin': isin,
                'quantity': holding.get('quantity'),
                'market_value': market_value,
                'weight_pct': weight_pct,
                'currency': holding.get('currency')
            }
        else:
            context['current_holding'] = None
    
    # Add summary data if available
    if summary:
        context['concentration_count'] = summary.get('concentration', {}).get('holdings_over_10pct', 0)
        context['recent_change'] = summary.get('recent_changes')
    
    return context


def _load_lens(repo_root: Path, lens_name: str) -> str:
    """Load investor lens markdown file"""
    lens_path = repo_root / 'analysis' / 'lenses' / f'{lens_name}.md'
    
    if not lens_path.exists():
        return f"[Lens {lens_name} not found]"
    
    try:
        with open(lens_path, 'r') as f:
            return f.read()
    except Exception:
        return f"[Error loading lens {lens_name}]"


def _generate_decision_framing(
    action: str,
    isin: Optional[str],
    name: Optional[str],
    context: Dict[str, Any],
    notes: Optional[str]
) -> List[str]:
    """Generate decision framing section"""
    lines = []
    
    # What decision
    if action == 'new':
        if name:
            lines.append(f"**Decision:** Consider initiating new position in {name}")
        else:
            lines.append("**Decision:** Consider initiating new position")
    elif action == 'add':
        if context.get('current_holding'):
            holding_name = context['current_holding']['name']
            current_weight = context['current_holding']['weight_pct']
            lines.append(f"**Decision:** Consider adding to existing position in {holding_name}")
            lines.append(f"**Current Weight:** {current_weight:.2f}%")
        else:
            lines.append(f"**Decision:** Consider adding to position (ISIN: {isin})")
            lines.append("**Warning:** Position not found in current portfolio")
    elif action == 'trim':
        if context.get('current_holding'):
            holding_name = context['current_holding']['name']
            current_weight = context['current_holding']['weight_pct']
            lines.append(f"**Decision:** Consider reducing position in {holding_name}")
            lines.append(f"**Current Weight:** {current_weight:.2f}%")
        else:
            lines.append(f"**Decision:** Consider trimming position (ISIN: {isin})")
            lines.append("**Warning:** Position not found in current portfolio")
    elif action == 'exit':
        if context.get('current_holding'):
            holding_name = context['current_holding']['name']
            lines.append(f"**Decision:** Consider exiting position in {holding_name}")
        else:
            lines.append(f"**Decision:** Consider exiting position (ISIN: {isin})")
            lines.append("**Warning:** Position not found in current portfolio")
    elif action == 'hold':
        if context.get('current_holding'):
            holding_name = context['current_holding']['name']
            lines.append(f"**Decision:** Review and maintain current position in {holding_name}")
        elif isin:
            lines.append(f"**Decision:** Review position (ISIN: {isin})")
        else:
            lines.append("**Decision:** General portfolio review")
    
    lines.append("")
    
    # What changed
    if context.get('recent_change') and context['recent_change'].get('delta_pct'):
        delta_pct = context['recent_change']['delta_pct'] * 100
        lines.append(f"**Recent Portfolio Change:** {delta_pct:+.1f}% since last snapshot")
    else:
        lines.append("**Recent Portfolio Change:** No explanation available")
    
    lines.append("")
    
    # User notes
    if notes:
        lines.append(f"**Context Notes:** {notes}")
        lines.append("")
    
    # Known vs unknown
    lines.append("**Known:**")
    lines.append(f"- Portfolio value: {context['total_value']:,.2f} {context['base_currency']}")
    lines.append(f"- Total holdings: {context['holdings_count']}")
    if context.get('current_holding'):
        h = context['current_holding']
        lines.append(f"- Current position: {h['market_value']:,.2f} {h['currency']} ({h['weight_pct']:.2f}%)")
    lines.append("")
    
    lines.append("**Unknown:**")
    lines.append("- Current market conditions")
    lines.append("- Future price movements")
    lines.append("- Business fundamentals (use valuation tools separately)")
    lines.append("- News or external events")
    
    return lines


def _generate_portfolio_context_section(context: Dict[str, Any]) -> List[str]:
    """Generate portfolio context section"""
    lines = []
    
    if context.get('current_holding'):
        h = context['current_holding']
        lines.append(f"**Current Weight:** {h['weight_pct']:.2f}%")
        lines.append(f"**Market Value:** {h['market_value']:,.2f} {h['currency']}")
        lines.append(f"**Quantity:** {h['quantity']}")
        lines.append("")
    else:
        lines.append("**Current Weight:** 0% (not in portfolio)")
        lines.append("")
    
    # Concentration impact
    if context.get('concentration_count'):
        lines.append(f"**Concentration Context:** Portfolio has {context['concentration_count']} positions over 10%")
    else:
        lines.append("**Concentration Context:** No positions over 10%")
    
    lines.append("")
    lines.append("**Correlation Notes:** [Manual analysis required - not computed automatically]")
    lines.append("")
    
    # Recent drivers
    if context.get('recent_change') and context['recent_change'].get('top_drivers'):
        lines.append("**Recent Portfolio Drivers:**")
        for driver in context['recent_change']['top_drivers'][:3]:
            name = driver.get('name', driver.get('currency', driver.get('type')))
            contrib = driver.get('contribution_abs', 0)
            lines.append(f"- {name}: {contrib:+,.2f}")
    else:
        lines.append("**Recent Portfolio Drivers:** [No explanation data available]")
    
    return lines


def _generate_lens_section(lens_name: str, context: Dict[str, Any]) -> List[str]:
    """Generate lens-specific analysis prompts"""
    lines = []
    
    if lens_name == 'marks':
        lines.append("### Howard Marks — Risk & Cycles")
        lines.append("")
        lines.append("**Questions to consider:**")
        lines.append("")
        lines.append("- **Permanent capital loss:** Where could this position go to zero or suffer irreversible decline?")
        lines.append("- **Assumptions:** What must be true for this decision to be correct?")
        lines.append("- **What's priced in:** What does consensus believe? Am I accepting or disagreeing with it?")
        lines.append("- **Cycle positioning:** Where are we in the economic/market cycle? Is this defensive or aggressive?")
        lines.append("- **Concentration risk:** How does this change portfolio concentration and correlation?")
        lines.append("")
        lines.append("**Your analysis:**")
        lines.append("[TODO: Fill in your thinking based on the questions above]")
    
    elif lens_name == 'munger':
        lines.append("### Charlie Munger — Understanding & Incentives")
        lines.append("")
        lines.append("**Questions to consider:**")
        lines.append("")
        lines.append("- **Understanding:** Can I explain this business in simple terms? Do I know how it makes money?")
        lines.append("- **Predictability:** Can I predict this business's state in 5-10 years?")
        lines.append("- **Self-deception:** Where could I be fooling myself? Am I in my circle of competence?")
        lines.append("- **Incentives:** What are management's incentives? Are they aligned with shareholders?")
        lines.append("- **Complexity:** Is this simple or complex? Am I paying for unnecessary complexity?")
        lines.append("- **Mistakes:** What behavioral errors might I be making (anchoring, confirmation bias, social proof)?")
        lines.append("")
        lines.append("**Your analysis:**")
        lines.append("[TODO: Fill in your thinking based on the questions above]")
    
    elif lens_name == 'klarman':
        lines.append("### Seth Klarman — Margin of Safety")
        lines.append("")
        lines.append("**Questions to consider:**")
        lines.append("")
        lines.append("- **Downside protection:** What protects me if I'm wrong? What's the worst case?")
        lines.append("- **Margin of safety:** How much cushion is there between price and value?")
        lines.append("- **Investing vs. speculating:** Is this based on value or on price appreciation hopes?")
        lines.append("- **Catalyst:** What's the path to value realization? Or am I just hoping?")
        lines.append("- **Liquidity:** Can I exit easily if needed? What's the bid-ask spread?")
        lines.append("- **Optionality:** Do I have flexibility, or am I forced into this decision?")
        lines.append("")
        lines.append("**Your analysis:**")
        lines.append("[TODO: Fill in your thinking based on the questions above]")
    
    return lines


def _generate_decision_memo(
    action: str,
    isin: Optional[str],
    name: Optional[str],
    context: Dict[str, Any],
    notes: Optional[str],
    lenses: List[str]
) -> str:
    """Generate complete decision memo markdown"""
    lines = []
    
    # Header
    if name:
        title = name
    elif context.get('current_holding'):
        title = f"{context['current_holding']['name']} ({isin})"
    elif isin:
        title = isin
    else:
        title = "Portfolio Decision"
    
    lines.append(f"# Decision Memo: {title}")
    lines.append("")
    lines.append(f"**Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"**Action:** {action.upper()}")
    lines.append(f"**Snapshot ID:** {context['snapshot_id']}")
    lines.append(f"**Portfolio Context:** {context['total_value']:,.0f} {context['base_currency']}, {context['holdings_count']} holdings")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Section 1: Decision Framing
    lines.append("## 1. Decision Framing (Facts Only)")
    lines.append("")
    lines.extend(_generate_decision_framing(action, isin, name, context, notes))
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Section 2: Portfolio Context
    lines.append("## 2. Portfolio Context")
    lines.append("")
    lines.extend(_generate_portfolio_context_section(context))
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Section 3: Investor Lens Review
    lines.append("## 3. Investor Lens Review")
    lines.append("")
    
    for lens in lenses:
        lines.extend(_generate_lens_section(lens, context))
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Section 4: Disconfirming Evidence
    lines.append("## 4. Disconfirming Evidence")
    lines.append("")
    lines.append("**What would make this decision wrong?**")
    lines.append("[TODO: List specific conditions that would invalidate your thesis]")
    lines.append("")
    lines.append("**What evidence would change my mind?**")
    lines.append("[TODO: Define specific observable triggers for reconsidering]")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Section 5: Alternatives Considered
    lines.append("## 5. Alternatives Considered")
    lines.append("")
    lines.append("- **Do nothing:** [Evaluate explicitly - sometimes best choice]")
    lines.append("- **Reduce exposure elsewhere:** [Consider if this is about position sizing vs. security selection]")
    lines.append("- **Delay decision:** [Is there value in waiting for more information?]")
    lines.append("- **Other options:** [List any other alternatives]")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Section 6: Decision Status
    lines.append("## 6. Decision Status")
    lines.append("")
    lines.append("- ☐ **Proceed** - Move forward with this decision")
    lines.append("- ☐ **Delay** - Wait for more information or better opportunity")
    lines.append("- ☐ **Reject** - Do not take this action")
    lines.append("")
    lines.append("**Rationale (plain language):**")
    lines.append("")
    lines.append("[TODO: Explain your decision in 2-3 clear sentences]")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Section 7: Follow-ups & Triggers
    lines.append("## 7. Follow-ups & Triggers")
    lines.append("")
    lines.append("**What should I monitor?**")
    lines.append("- [TODO: List specific metrics, events, or conditions to track]")
    lines.append("")
    lines.append("**What would force a revisit?**")
    lines.append("- [TODO: Define clear triggers that require reassessment]")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Footer
    lines.append("**Note:** This decision memo is a structured thinking tool. It does not constitute")
    lines.append("financial advice or a recommendation. All portfolio decisions require human judgment")
    lines.append("and should be made with full consideration of individual circumstances.")
    
    return "\n".join(lines)


def run_decide(
    isin: Optional[str],
    action: str,
    name: Optional[str],
    notes: Optional[str],
    snapshot_path: Path,
    lenses: List[str],
    repo_root: Path,
    emit_template_only: bool = False
) -> Tuple[str, Path]:
    """
    Main entry point for decide command.
    
    Args:
        isin: Security ISIN (optional for new positions)
        action: Decision action (new/add/trim/exit/hold)
        name: Name for new positions
        notes: User context notes
        snapshot_path: Path to portfolio snapshot
        lenses: List of lenses to apply
        repo_root: Repository root
        emit_template_only: If True, skip analysis and just create template
    
    Returns:
        Tuple of (memo_text, output_path)
    
    Raises:
        DecideError: If decision memo generation fails
    """
    # Validate action
    if action not in VALID_ACTIONS:
        raise DecideError(f"Invalid action: {action}. Must be one of: {', '.join(VALID_ACTIONS)}")
    
    # Validate inputs
    if action == 'new' and not name and not isin:
        raise DecideError("For 'new' action, must provide --name or --isin")
    
    if action in ['add', 'trim', 'exit'] and not isin:
        raise DecideError(f"For '{action}' action, must provide --isin")
    
    # Load data
    snapshot = _load_snapshot(snapshot_path)
    summary = _load_summary(repo_root) if not emit_template_only else None
    
    # Extract portfolio context
    context = _extract_portfolio_context(isin, action, snapshot, summary)
    
    # Generate memo
    memo = _generate_decision_memo(action, isin, name, context, notes, lenses)
    
    # Create filename
    date_str = datetime.utcnow().strftime('%Y-%m-%d')
    
    if isin:
        identifier = isin
    elif name:
        identifier = _slugify(name)
    else:
        identifier = "portfolio_review"
    
    filename = f"{date_str}_{identifier}_{action}.md"
    
    # Write to file
    decisions_dir = repo_root / 'decisions'
    decisions_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = decisions_dir / filename
    
    with open(output_path, 'w') as f:
        f.write(memo)
    
    return memo, output_path
