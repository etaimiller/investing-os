# Schema Directory

This directory contains JSON schemas and format specifications for all Investment OS data structures.

## What Belongs Here

- **JSON schemas** - Formal schema definitions for data validation
- **Format specifications** - Templates and examples for data formats
- **Validation rules** - Data quality and consistency requirements

## Core Schemas

### portfolio-state.schema.json
**Purpose**: Defines the complete structure for portfolio snapshots

**Key Principles**:
- Facts only - no valuations or assumptions
- Market data is clearly separated from cost basis
- All currency amounts include currency code
- Derived values (like market_value) are explicitly marked

**Usage**: Validate portfolio snapshot JSON files against this schema

### valuation-model.schema.json
**Purpose**: Defines structure for security valuation analysis

**Key Principles**:
- Separates assumptions, facts, and calculated values
- All assumptions must be explicitly stated and justified
- Qualitative factors tracked alongside quantitative
- Links to assumption templates (e.g., conservative.yaml)

**Usage**: Validate valuation JSON files against this schema

### decision-memo.schema.json
**Purpose**: Defines structure for investment decision records

**Key Principles**:
- Complete audit trail of decision rationale
- Links to supporting valuations and research
- Separates facts, assumptions, and opinions
- Includes alternatives considered
- No automated execution - recommendations only

**Usage**: Validate decision memo JSON files against this schema

## Schema Design Principles

### Separation of Concerns
- **Facts** - Observable data from markets or filings
- **Assumptions** - Projections and estimates with rationale
- **Derived Values** - Calculations based on facts and assumptions
- **Opinions** - Qualitative assessments and judgments

### Conservative by Default
- Required fields enforce completeness
- Validation rules prevent invalid data
- Assumptions must be explicitly documented
- All values include units and currency

### Audit Trail
- Every schema includes timestamp and versioning
- Links between related documents (valuations → decisions)
- Metadata tracks data provenance
- Immutable snapshots preserve history

## File Naming Conventions

### Schema Files
- `{domain}-{entity}.schema.json` format
- Examples: `portfolio-state.schema.json`, `valuation-model.schema.json`

### Data Files Following Schemas
- Portfolio snapshots: `YYYY-MM-DD-HHMMSS.json`
- Valuations: `{TICKER}-valuation-YYYY-MM-DD.json`
- Decisions: `{TICKER}-decision-YYYY-MM-DD-HHMMSS.json`

## Schema Versioning

All schemas include a version field following semantic versioning:
- **Major version** - Breaking changes to structure
- **Minor version** - Backward-compatible additions
- **Patch version** - Clarifications and bug fixes

Current versions:
- portfolio-state: 1.0.0
- valuation-model: 1.0.0
- decision-memo: 1.0.0

## Validation

Schemas follow JSON Schema Draft 07 specification and can be validated using standard tools.

Example validation (conceptual):
```
validate-json --schema schema/portfolio-state.schema.json --data portfolio/snapshots/2024-01-15-143022.json
```

## TODO: User Input Required

**Schema Customization**:
- TODO: Are there additional fields needed for your specific use case?
- TODO: Should schemas enforce stricter validation rules?
- TODO: What custom metadata fields should be added?

**Data Sources**:
- TODO: Confirm Trade Republic export format matches portfolio schema assumptions
- TODO: What additional data sources need schema definitions?

## Notes

- Schemas are living documents - update as needs evolve
- Always increment version when changing schema structure
- Maintain backward compatibility when possible
- Document breaking changes in commit messages
- Test schema changes against existing data files