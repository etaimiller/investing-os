"""
Investment OS CLI - Main entrypoint

Dispatch-style CLI providing structured interface to Investment OS operations.
Uses stdlib only - no external dependencies.

Usage:
    investos status
    investos doctor
    investos validate --file <path> --schema <schema_path>
    investos scaffold decision --ticker <TICKER>
    investos scaffold valuation --ticker <TICKER>
    investos scaffold dossier --ticker <TICKER>
"""

import sys
import argparse
from pathlib import Path
from typing import List

# Import our modules
from . import __version__
from .utils import find_repo_root, count_files, find_latest_file
from .config import load_config
from .logging import create_logger
from .doctor import run_health_check
from .validate import validate_with_schema, validate_json_file, JSONSCHEMA_AVAILABLE
from .scaffold import (
    scaffold_decision_memo,
    scaffold_valuation_input,
    scaffold_research_dossier
)
from .ingest import ingest_pdf, IngestError


def cmd_status(args, repo_root: Path, config, logger) -> int:
    """Print repository status"""
    print("Investment OS Status")
    print("=" * 60)
    print()
    
    # Check for latest snapshot
    snapshots_dir = repo_root / config.snapshots_dir
    latest_snapshot = find_latest_file(snapshots_dir, '*.json')
    
    if latest_snapshot:
        print(f"✓ Latest snapshot: {latest_snapshot.name}")
        logger.add_path(latest_snapshot)
        logger.set_info('latest_snapshot', str(latest_snapshot.name))
    else:
        print("○ No portfolio snapshots found")
        logger.add_warning("No portfolio snapshots found")
    
    # Count raw PDFs
    raw_dir = repo_root / config.portfolio_raw_dir
    pdf_count = count_files(raw_dir, '*.pdf')
    print(f"  Raw PDFs in {config.portfolio_raw_dir}: {pdf_count}")
    logger.set_info('raw_pdf_count', pdf_count)
    
    # Check for last run log
    logs_dir = repo_root / config.logs_dir
    if logs_dir.exists():
        # Find most recent log
        all_logs = list(logs_dir.rglob('*.json'))
        if all_logs:
            latest_log = max(all_logs, key=lambda p: p.stat().st_mtime)
            print(f"  Last run log: {latest_log.relative_to(repo_root)}")
            logger.set_info('last_log', str(latest_log.relative_to(repo_root)))
        else:
            print("  No run logs found")
    
    print()
    print("Run 'investos doctor' for complete health check")
    print("=" * 60)
    
    logger.success("Status check completed")
    return 0


def cmd_doctor(args, repo_root: Path, config, logger) -> int:
    """Run health checks"""
    health = run_health_check(repo_root, config)
    
    # Print summary
    print(health.summary())
    
    # Log results
    logger.set_info('checks_passed', health.checks_passed)
    logger.set_info('checks_failed', health.checks_failed)
    logger.set_info('warnings_count', len(health.warnings))
    
    if health.is_healthy:
        logger.success("Health check passed")
        return 0
    else:
        logger.failure("Health check failed")
        return 1


def cmd_validate(args, repo_root: Path, config, logger) -> int:
    """Validate JSON file against schema"""
    file_path = Path(args.file)
    schema_path = Path(args.schema) if args.schema else None
    
    # Make paths absolute if needed
    if not file_path.is_absolute():
        file_path = repo_root / file_path
    if schema_path and not schema_path.is_absolute():
        schema_path = repo_root / schema_path
    
    logger.add_path(file_path)
    if schema_path:
        logger.add_path(schema_path)
    
    print(f"Validating: {file_path.relative_to(repo_root)}")
    
    if schema_path:
        print(f"Against schema: {schema_path.relative_to(repo_root)}")
        print()
        if JSONSCHEMA_AVAILABLE:
            print("Using JSON Schema Draft-07 validation")
        else:
            print("NOTE: jsonschema library not installed")
            print("      Performing basic structure validation only")
            print("      Install with: pip install jsonschema>=4.17.0")
        print()
        
        result = validate_with_schema(file_path, schema_path)
    else:
        print("Performing JSON syntax validation only (no schema specified)")
        print()
        result = validate_json_file(file_path)
    
    print(result.summary())
    
    if result.valid:
        logger.success("Validation passed")
        return 0
    else:
        logger.failure("Validation failed")
        for error in result.errors:
            logger.add_error(error)
        return 1


def cmd_scaffold_decision(args, repo_root: Path, config, logger) -> int:
    """Scaffold decision memo"""
    ticker = args.ticker.upper()
    
    print(f"Creating decision memo for {ticker}...")
    
    filepath = scaffold_decision_memo(repo_root, ticker)
    logger.add_path(filepath)
    
    rel_path = filepath.relative_to(repo_root)
    print(f"✓ Created: {rel_path}")
    print()
    print("Next steps:")
    print(f"  1. Edit {rel_path}")
    print("  2. Fill in all TODO sections")
    print("  3. Link to valuation and research files")
    print("  4. Get human approval before taking action")
    
    logger.success(f"Created decision memo for {ticker}")
    logger.set_info('ticker', ticker)
    logger.set_info('filepath', str(rel_path))
    
    return 0


def cmd_scaffold_valuation(args, repo_root: Path, config, logger) -> int:
    """Scaffold valuation input"""
    ticker = args.ticker.upper()
    
    print(f"Creating valuation input template for {ticker}...")
    
    filepath = scaffold_valuation_input(repo_root, ticker)
    logger.add_path(filepath)
    
    rel_path = filepath.relative_to(repo_root)
    print(f"✓ Created: {rel_path}")
    print()
    print("Next steps:")
    print(f"  1. Edit {rel_path}")
    print("  2. Fill in financial inputs from 10-K or annual report")
    print("  3. Adjust growth and discount rate assumptions")
    print("  4. Create full valuation model (Step 5)")
    
    logger.success(f"Created valuation input for {ticker}")
    logger.set_info('ticker', ticker)
    logger.set_info('filepath', str(rel_path))
    
    return 0


def cmd_scaffold_dossier(args, repo_root: Path, config, logger) -> int:
    """Scaffold research dossier"""
    ticker = args.ticker.upper()
    
    print(f"Creating research dossier for {ticker}...")
    
    filepath = scaffold_research_dossier(repo_root, ticker)
    logger.add_path(filepath)
    
    rel_path = filepath.relative_to(repo_root)
    print(f"✓ Created: {rel_path}")
    print(f"✓ Created: research/{ticker}/README.md")
    print()
    print("Next steps:")
    print(f"  1. Edit {rel_path}")
    print("  2. Document business, moat, risks, thesis")
    print("  3. Add sources and research log entries")
    print("  4. Link from decision memos and valuations")
    
    logger.success(f"Created research dossier for {ticker}")
    logger.set_info('ticker', ticker)
    logger.set_info('filepath', str(rel_path))
    
    return 0


def cmd_ingest(args, repo_root: Path, config, logger) -> int:
    """Ingest Trade Republic PDF"""
    pdf_path = Path(args.pdf)
    account_name = args.account if hasattr(args, 'account') and args.account else 'unknown'
    export_csv = not args.no_csv if hasattr(args, 'no_csv') else True
    debug_parse = args.debug_parse if hasattr(args, 'debug_parse') else False
    
    # Make path absolute if needed
    if not pdf_path.is_absolute():
        pdf_path = Path.cwd() / pdf_path
    
    print(f"Ingesting Trade Republic PDF...")
    print(f"  Source: {pdf_path}")
    print(f"  Account: {account_name}")
    if debug_parse:
        print(f"  Debug mode: ENABLED")
    print()
    
    try:
        result = ingest_pdf(pdf_path, repo_root, config, account_name, export_csv, debug_parse)
        
        # Log paths
        if result.get('raw_pdf_path'):
            logger.add_path(result['raw_pdf_path'])
        if result.get('snapshot_path'):
            logger.add_path(result['snapshot_path'])
        if result.get('csv_path'):
            logger.add_path(result['csv_path'])
        if result.get('latest_path'):
            logger.add_path(result['latest_path'])
        
        # Print results
        print("✓ Ingestion complete!")
        print()
        
        if result.get('raw_pdf_path'):
            print(f"  Raw PDF: {result['raw_pdf_path'].relative_to(repo_root)}")
        
        if result.get('snapshot_path'):
            print(f"  Snapshot: {result['snapshot_path'].relative_to(repo_root)}")
        
        if result.get('latest_path'):
            print(f"  Latest: {result['latest_path'].relative_to(repo_root)}")
        
        if result.get('csv_path'):
            print(f"  CSV export: {result['csv_path'].relative_to(repo_root)}")
        
        print()
        print(f"  Holdings extracted: {result.get('holdings_count', 0)}")
        
        # Warnings
        if result.get('warnings'):
            print()
            print("Warnings:")
            for warning in result['warnings']:
                print(f"  ⚠ {warning}")
                logger.add_warning(warning)
        
        logger.set_info('holdings_count', result.get('holdings_count', 0))
        logger.set_info('account', account_name)
        logger.success("PDF ingestion completed")
        
        return 0
    
    except IngestError as e:
        print(f"\nError: {e}", file=sys.stderr)
        logger.failure(str(e))
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        logger.failure(f"Unexpected error: {e}")
        return 1


def main(argv: List[str] = None) -> int:
    """Main CLI entrypoint"""
    if argv is None:
        argv = sys.argv[1:]
    
    # Find repo root
    repo_root = find_repo_root()
    
    # Load config
    try:
        config = load_config(repo_root)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Run from repository root or ensure config.json exists", file=sys.stderr)
        return 1
    
    # Create parser
    parser = argparse.ArgumentParser(
        description='Investment OS - File-based portfolio management',
        prog='investos'
    )
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # status command
    subparsers.add_parser('status', help='Show repository status')
    
    # doctor command
    subparsers.add_parser('doctor', help='Run health checks')
    
    # validate command
    validate_parser = subparsers.add_parser('validate', help='Validate JSON file')
    validate_parser.add_argument('--file', required=True, help='File to validate')
    validate_parser.add_argument('--schema', help='Schema file to validate against')
    
    # ingest command
    ingest_parser = subparsers.add_parser('ingest', help='Ingest Trade Republic PDF')
    ingest_parser.add_argument('--pdf', required=True, help='Path to Trade Republic PDF')
    ingest_parser.add_argument('--account', help='Account name (default: unknown)')
    ingest_parser.add_argument('--no-csv', action='store_true', help='Skip CSV export')
    ingest_parser.add_argument('--debug-parse', action='store_true', help='Enable debug output for PDF parsing')
    
    # scaffold command with subcommands
    scaffold_parser = subparsers.add_parser('scaffold', help='Create templates')
    scaffold_subparsers = scaffold_parser.add_subparsers(dest='scaffold_type', help='Template type')
    
    decision_parser = scaffold_subparsers.add_parser('decision', help='Decision memo')
    decision_parser.add_argument('--ticker', required=True, help='Security ticker')
    
    valuation_parser = scaffold_subparsers.add_parser('valuation', help='Valuation input')
    valuation_parser.add_argument('--ticker', required=True, help='Security ticker')
    
    dossier_parser = scaffold_subparsers.add_parser('dossier', help='Research dossier')
    dossier_parser.add_argument('--ticker', required=True, help='Security ticker')
    
    # Parse args
    args = parser.parse_args(argv)
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Create logger
    command_name = f"{args.command}"
    if args.command == 'scaffold' and hasattr(args, 'scaffold_type'):
        command_name = f"scaffold_{args.scaffold_type}"
    
    logger = create_logger(repo_root, config.logs_dir, command_name, argv)
    
    try:
        # Dispatch to command handler
        if args.command == 'status':
            return cmd_status(args, repo_root, config, logger)
        elif args.command == 'doctor':
            return cmd_doctor(args, repo_root, config, logger)
        elif args.command == 'validate':
            return cmd_validate(args, repo_root, config, logger)
        elif args.command == 'ingest':
            return cmd_ingest(args, repo_root, config, logger)
        elif args.command == 'scaffold':
            if args.scaffold_type == 'decision':
                return cmd_scaffold_decision(args, repo_root, config, logger)
            elif args.scaffold_type == 'valuation':
                return cmd_scaffold_valuation(args, repo_root, config, logger)
            elif args.scaffold_type == 'dossier':
                return cmd_scaffold_dossier(args, repo_root, config, logger)
            else:
                print(f"Unknown scaffold type: {args.scaffold_type}", file=sys.stderr)
                return 1
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            return 1
    
    except Exception as e:
        logger.failure(str(e))
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    finally:
        # Always write log
        log_path = logger.write()
        print(f"\nRun log: {log_path.relative_to(repo_root)}")


if __name__ == '__main__':
    sys.exit(main())
