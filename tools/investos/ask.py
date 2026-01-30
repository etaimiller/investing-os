"""
Portfolio Question Answering

Produces narrative insights by combining portfolio facts with investor lenses.
NO external APIs, NO live data, NO hallucinated numbers.

Output: analysis/answers/<timestamp>_<slug>.md
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple


class AskError(Exception):
    """Raised when question answering fails"""
    pass


def _slugify(text: str) -> str:
    """Convert text to URL-safe slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '_', text)
    return text[:50]


def _select_relevant_lenses(question: str) -> List[str]:
    """
    Select which investor lenses are most relevant to the question.
    Returns list of lens names (e.g., ['marks', 'klarman'])
    """
    question_lower = question.lower()
    lenses = []
    
    # Marks lens: risk, cycles, what's priced in, concentration
    marks_keywords = [
        'risk', 'cycle', 'exposed', 'exposure', 'impair', 'permanent loss',
        'what could go wrong', 'downside', 'priced in', 'consensus',
        'concentration', 'correlated', 'worry', 'marks'
    ]
    
    # Munger lens: understanding, incentives, moats, psychology, simplicity
    munger_keywords = [
        'understand', 'know', 'competence', 'incentive', 'management',
        'moat', 'advantage', 'competitive', 'simple', 'complex',
        'mistake', 'bias', 'psychology', 'munger'
    ]
    
    # Klarman lens: margin of safety, value, catalyst, liquidity, tangibles
    klarman_keywords = [
        'margin', 'safety', 'value', 'cheap', 'expensive', 'catalyst',
        'liquid', 'asset', 'tangible', 'downside protection',
        'speculation', 'klarman', 'worth'
    ]
    
    # Score each lens
    marks_score = sum(1 for kw in marks_keywords if kw in question_lower)
    munger_score = sum(1 for kw in munger_keywords if kw in question_lower)
    klarman_score = sum(1 for kw in klarman_keywords if kw in question_lower)
    
    # If explicit name, prioritize that lens
    if 'marks' in question_lower:
        lenses.append('marks')
    if 'munger' in question_lower:
        lenses.append('munger')
    if 'klarman' in question_lower:
        lenses.append('klarman')
    
    # If no explicit names, select by score
    if not lenses:
        scores = [
            ('marks', marks_score),
            ('munger', munger_score),
            ('klarman', klarman_score)
        ]
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Take top scoring lens, or top 2 if tied
        if scores[0][1] > 0:
            lenses.append(scores[0][0])
            if scores[1][1] > 0 and scores[1][1] >= scores[0][1] * 0.7:
                lenses.append(scores[1][0])
    
    # Default to all three if question is too generic
    if not lenses:
        lenses = ['marks', 'munger', 'klarman']
    
    return lenses


def _load_summary(repo_root: Path) -> Dict[str, Any]:
    """Load portfolio summary from analysis/state/summary.json"""
    summary_path = repo_root / 'analysis' / 'state' / 'summary.json'
    
    if not summary_path.exists():
        raise AskError(
            "No portfolio summary found. Run 'investos summarize' first."
        )
    
    try:
        with open(summary_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise AskError(f"Failed to load summary: {e}")


def _load_lens(repo_root: Path, lens_name: str) -> str:
    """Load investor lens markdown file"""
    lens_path = repo_root / 'analysis' / 'lenses' / f'{lens_name}.md'
    
    if not lens_path.exists():
        raise AskError(f"Lens not found: {lens_name}")
    
    try:
        with open(lens_path, 'r') as f:
            return f.read()
    except Exception as e:
        raise AskError(f"Failed to load lens {lens_name}: {e}")


def _extract_observations(summary: Dict[str, Any]) -> List[str]:
    """Extract factual observations from portfolio summary"""
    observations = []
    
    totals = summary['portfolio_totals']
    currency = totals['base_currency']
    
    # Total value
    observations.append(
        f"Portfolio value: {totals['total_portfolio_value']:,.0f} {currency}"
    )
    
    # Holdings count
    counts = summary['holdings_count']
    observations.append(
        f"Holdings: {counts['total']} positions"
    )
    
    # Type breakdown
    type_breakdown = summary['security_type_breakdown']
    if type_breakdown:
        type_summary = ", ".join([
            f"{data['weight_pct']:.0f}% {sec_type}"
            for sec_type, data in sorted(
                type_breakdown.items(),
                key=lambda x: x[1]['weight_pct'],
                reverse=True
            )
        ])
        observations.append(f"Allocation: {type_summary}")
    
    # Top holdings
    top = summary['top_holdings']
    if top:
        top_names = [f"{h['name'][:30]} ({h['weight_pct']:.0f}%)" for h in top[:3]]
        observations.append(f"Top holdings: {', '.join(top_names)}")
    
    # Concentration
    concentration = summary['concentration']
    if concentration['holdings_over_10pct'] > 0:
        observations.append(
            f"Concentration: {concentration['holdings_over_10pct']} holdings over 10%"
        )
    
    # Recent changes
    if summary.get('recent_changes') and summary['recent_changes'].get('delta_pct') is not None:
        delta_pct = summary['recent_changes']['delta_pct'] * 100
        observations.append(
            f"Recent change: {delta_pct:+.1f}% since last snapshot"
        )
    
    return observations


def _generate_risks(summary: Dict[str, Any], lenses: List[str]) -> List[str]:
    """Generate risk considerations based on portfolio facts and lenses"""
    risks = []
    
    # Concentration risk
    concentration = summary['concentration']
    if concentration['holdings_over_10pct'] > 0:
        flags = concentration['flags']
        if 'marks' in lenses or 'klarman' in lenses:
            top_name = flags[0]['name'][:40]
            risks.append(
                f"Concentration risk: {flags[0]['weight_pct']:.0f}% in {top_name} "
                "creates single-position downside exposure"
            )
    
    # ETF vs Stock balance
    type_breakdown = summary['security_type_breakdown']
    etf_pct = type_breakdown.get('ETF', {}).get('weight_pct', 0)
    stock_pct = type_breakdown.get('Stock', {}).get('weight_pct', 0)
    
    if 'munger' in lenses:
        if stock_pct > 50:
            risks.append(
                f"Individual stock concentration: {stock_pct:.0f}% in stocks "
                "requires deep understanding of each business"
            )
    
    # Type classification uncertainty
    other_pct = type_breakdown.get('Other', {}).get('weight_pct', 0)
    if other_pct > 20:
        risks.append(
            f"Classification uncertainty: {other_pct:.0f}% in 'Other' category "
            "suggests complex or hybrid securities"
        )
    
    # Data quality
    quality = summary['data_quality']
    if quality['holdings_without_market_value'] > 0:
        risks.append(
            f"Data gaps: {quality['holdings_without_market_value']} holdings "
            "without market values affect accuracy"
        )
    
    return risks


def _generate_questions(summary: Dict[str, Any], lenses: List[str]) -> List[str]:
    """Generate open questions based on lenses"""
    questions = []
    
    top_holdings = summary['top_holdings'][:5]
    
    if 'marks' in lenses:
        questions.append(
            "Where are we in the cycle? Are these holdings positioned defensively or aggressively?"
        )
        questions.append(
            "What consensus assumptions are embedded in current prices?"
        )
    
    if 'munger' in lenses:
        if top_holdings:
            questions.append(
                f"Do I truly understand how {top_holdings[0]['name'][:30]} makes money? "
                "Can I predict its state in 10 years?"
            )
        questions.append(
            "What are management incentives in my largest holdings? "
            "Are they owner-operators or hired hands?"
        )
    
    if 'klarman' in lenses:
        questions.append(
            "What is my actual margin of safety in each position? "
            "What's the downside if my thesis is wrong?"
        )
        questions.append(
            "Which positions have clear catalysts for value realization?"
        )
    
    return questions


def _generate_attention_items(summary: Dict[str, Any], lenses: List[str]) -> List[str]:
    """Generate items that deserve attention"""
    items = []
    
    # Largest position
    top = summary['top_holdings']
    if top:
        top_holding = top[0]
        items.append(
            f"Review largest position: {top_holding['name'][:40]} "
            f"({top_holding['weight_pct']:.0f}%) - "
            "Ensure thesis is still valid and risk is acceptable"
        )
    
    # Concentration flags
    concentration = summary['concentration']
    if concentration['holdings_over_10pct'] >= 3:
        items.append(
            f"High concentration: {concentration['holdings_over_10pct']} positions over 10% - "
            "Consider correlation and combined downside"
        )
    
    # Recent changes
    if summary.get('recent_changes'):
        items.append(
            "Review recent portfolio changes - "
            "Understand what drove the change and whether it was intentional"
        )
    
    # ETF classification
    type_breakdown = summary['security_type_breakdown']
    if type_breakdown.get('Other', {}).get('count', 0) > 5:
        items.append(
            "Investigate 'Other' securities - "
            "Verify you understand structure and risks of non-standard holdings"
        )
    
    return items


def _generate_answer(
    question: str,
    summary: Dict[str, Any],
    lenses: List[str]
) -> str:
    """
    Generate structured markdown answer to question.
    
    Structure:
    - Question
    - Observations (facts)
    - Risks
    - Open Questions
    - What Deserves Attention
    """
    observations = _extract_observations(summary)
    risks = _generate_risks(summary, lenses)
    open_questions = _generate_questions(summary, lenses)
    attention = _generate_attention_items(summary, lenses)
    
    # Build markdown
    lines = []
    lines.append(f"# Portfolio Analysis: {question}")
    lines.append("")
    lines.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"**Snapshot:** {summary['snapshot']['snapshot_id']}")
    lines.append(f"**Lenses Applied:** {', '.join([l.title() for l in lenses])}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Observations
    lines.append("## Observations (Facts)")
    lines.append("")
    for obs in observations:
        lines.append(f"- {obs}")
    lines.append("")
    
    # Risks
    lines.append("## Risks to Consider")
    lines.append("")
    if risks:
        for risk in risks:
            lines.append(f"- {risk}")
    else:
        lines.append("- No specific risk flags identified from current data")
    lines.append("")
    
    # Open questions
    lines.append("## Open Questions")
    lines.append("")
    for q in open_questions:
        lines.append(f"- {q}")
    lines.append("")
    
    # Attention items
    lines.append("## What Deserves Attention")
    lines.append("")
    for item in attention:
        lines.append(f"- {item}")
    lines.append("")
    
    # Footer
    lines.append("---")
    lines.append("")
    lines.append("**Note:** This analysis is based on portfolio state only. ")
    lines.append("No external data, valuations, or market predictions are included. ")
    lines.append("All observations are derived from the most recent snapshot.")
    lines.append("")
    
    return "\n".join(lines)


def run_ask(question: str, repo_root: Path, config) -> Tuple[str, Path]:
    """
    Main entry point for ask command.
    
    Args:
        question: User's question
        repo_root: Repository root
        config: Configuration object
    
    Returns:
        Tuple of (answer_text, output_path)
    
    Raises:
        AskError: If question answering fails
    """
    # Load summary
    summary = _load_summary(repo_root)
    
    # Select relevant lenses
    lenses = _select_relevant_lenses(question)
    
    # Generate answer
    answer = _generate_answer(question, summary, lenses)
    
    # Write to file
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    slug = _slugify(question)
    filename = f"{timestamp}_{slug}.md"
    
    answers_dir = repo_root / 'analysis' / 'answers'
    answers_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = answers_dir / filename
    
    with open(output_path, 'w') as f:
        f.write(answer)
    
    return answer, output_path


def _create_short_summary(answer_text: str) -> str:
    """Create short console-friendly summary from full answer"""
    lines = answer_text.split('\n')
    
    # Extract key sections
    output = []
    current_section = None
    section_lines = []
    
    for line in lines:
        if line.startswith('## '):
            if current_section and section_lines:
                # Save previous section (first 3 items only)
                output.append(f"\n{current_section}")
                for item in section_lines[:3]:
                    output.append(item)
                if len(section_lines) > 3:
                    output.append(f"  ... and {len(section_lines) - 3} more")
            
            current_section = line
            section_lines = []
        elif line.startswith('- ') and current_section:
            section_lines.append(line)
    
    # Add last section
    if current_section and section_lines:
        output.append(f"\n{current_section}")
        for item in section_lines[:3]:
            output.append(item)
        if len(section_lines) > 3:
            output.append(f"  ... and {len(section_lines) - 3} more")
    
    return '\n'.join(output)
