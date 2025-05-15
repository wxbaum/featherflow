#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Command-line interface for Featherflow
"""

import sys
import argparse
import logging
import json

# Use relative imports for the package
from . import core
from . import utils
from . import parser
from . import executor

def main():
    """Main entry point for the CLI"""
    parser = argparse.ArgumentParser(description="Featherflow - Ultra-lightweight workflow orchestration tool")
    
    # Global options
    parser.add_argument("--flows-dir", "-f", default="./flows", help="Directory containing flow JSON files")
    parser.add_argument("--tasks-dir", "-t", default="./tasks", help="Directory containing task scripts")
    parser.add_argument("--output-dir", "-o", default="./featherflow_output", help="Directory for generated bash scripts and logs")
    parser.add_argument("--log-level", "-l", default="INFO", help="Logging level")
    
    # Subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available flows")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Execute a flow")
    run_parser.add_argument("flow_name", help="Name of the flow to run")
    run_parser.add_argument("--params", "-p", help="JSON string or path to JSON file with parameters")
    run_parser.add_argument("--dry-run", action="store_true", help="Generate script but don't execute it")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Initialize Featherflow
    featherflow = core.Featherflow(
        flows_dir=args.flows_dir,
        tasks_dir=args.tasks_dir,
        output_dir=args.output_dir
    )
    
    # Execute the requested command
    if args.command == "list":
        flows = featherflow.list_flows()
        print(f"Available flows: {flows}")
    elif args.command == "run":
        params = {}
        if args.params:
            # Parse params as JSON string or file
            if args.params.startswith("{"):
                params = json.loads(args.params)
            else:
                with open(args.params, "r") as f:
                    params = json.load(f)
        
        script_path = featherflow.execute_flow(
            args.flow_name,
            params=params,
            dry_run=args.dry_run
        )
        print(f"Script generated at: {script_path}")
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()