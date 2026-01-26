# Monitoring Directory

This directory contains portfolio monitoring rules, alerts, and daily digest generation.

## What Belongs Here

- **Monitoring rules** - Automated rules for portfolio tracking and alerts
- **Daily digests** - Generated daily portfolio summaries and insights
- **Alert configurations** - Thresholds and conditions for notifications
- **Performance tracking** - Portfolio performance metrics and trends

## File Naming Convention

- **Monitoring rules**: `rule-[name]-YYYY-MM-DD.json`
- **Daily digests**: `digest-YYYY-MM-DD.md`
- **Alert configurations**: `alerts-config-YYYY-MM-DD.json`
- **Performance reports**: `performance-YYYY-MM-DD.json`

## Monitoring Categories

1. **Price Movements** - Significant price changes in holdings
2. **Portfolio Drift** - Allocation changes from targets
3. **Valuation Changes** - Updates to intrinsic value estimates
4. **Risk Metrics** - Portfolio risk measurements and changes
5. **Corporate Actions** - Splits, dividends, mergers, acquisitions

## Workflow Integration

1. **Rule Definition** - Set up monitoring rules and thresholds
2. **Daily Processing** - Generate daily portfolio digest
3. **Alert Generation** - Create alerts when rules are triggered
4. **Performance Analysis** - Track portfolio performance over time
5. **Decision Support** - Provide monitoring insights for decisions

## When to Look Here

- **Daily review** - Check daily digest for portfolio updates
- **Alert investigation** - Review triggered alerts and determine actions
- **Performance review** - Analyze portfolio performance trends
- **Rule adjustment** - Update monitoring rules as needed

## Directory Structure

```
monitoring/
├── watch_rules.yaml   # Core monitoring rules and thresholds
├── rules/             # Monitoring rules and configurations
├── digests/           # Daily portfolio digests
├── alerts/            # Alert history and configurations
└── performance/       # Performance tracking and analysis
```

## Monitoring Rules

Core monitoring rules are defined in **watch_rules.yaml**.

**Rule categories**:
- Price movement thresholds (single-day and multi-day)
- Portfolio allocation drift monitoring
- Valuation change alerts
- Corporate action notifications
- Risk metric tracking

**Important**: All monitoring is for ALERTING only - never for automated trading. All alerts require human review and decision.

## Monitoring Rules Framework

**Price Movement Rules:**
- Percentage change thresholds
- Absolute price change thresholds
- Volume and volatility alerts

**Portfolio Allocation Rules:**
- Target allocation drift percentages
- Rebalancing trigger conditions
- Concentration limit alerts

**Valuation Monitoring:**
- Price vs intrinsic value divergence
- Margin of safety changes
- Valuation model updates

**Risk Monitoring:**
- Portfolio risk metric changes
- Individual security risk updates
- Market condition alerts

## Daily Digest Components

**Portfolio Summary:**
- Current portfolio value and allocation
- Daily change and performance
- Cash position and availability

**Holdings Updates:**
- Price movements and performance
- Corporate actions and events
- Valuation updates and changes

**Market Context:**
- Market conditions and trends
- Economic indicators
- Relevant news and events

## TODO: User Input Required

**Alert Thresholds:**
- TODO: What price movement percentages should trigger alerts?
- TODO: What portfolio drift percentages are acceptable?
- TODO: How should valuation changes be monitored?

**Digest Content:**
- TODO: What information should be included in daily digests?
- TODO: How should performance be presented and tracked?

**Monitoring Frequency:**
- TODO: How often should monitoring rules run?
- TODO: What time should daily digests be generated?

## Notes

- Monitoring is for awareness, not automated trading
- All alerts require human review and decision
- Conservative thresholds to avoid alert fatigue
- Focus on meaningful changes that require attention
- Daily digests provide portfolio context without overwhelming detail