#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Command-line interface for Featherflow
"""

import sys
import argparse
import logging
import json
import os
import time
import datetime
import shutil

# Use relative imports for the package
from . import core
from . import utils
from . import parser
from . import executor
from . import scheduler
from . import display  # Import the display module

def main():
    """Main entry point for the CLI"""
    parser = argparse.ArgumentParser(description="Featherflow - Ultra-lightweight workflow orchestration tool")
    
    # Global options
    parser.add_argument("--flows-dir", "-f", default="./flows", help="Directory containing flow JSON files")
    parser.add_argument("--tasks-dir", "-t", default="./tasks", help="Directory containing task scripts")
    parser.add_argument("--output-dir", "-o", default="./featherflow_output", help="Directory for generated bash scripts and logs")
    parser.add_argument("--log-level", "-l", default="INFO", help="Logging level")
    parser.add_argument("--log-dir", default=None, help="Directory for log files (optional)")
    parser.add_argument("--config-dir", default=None, help="Directory for configuration files (optional)")
    
    # Subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available flows")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Execute a flow")
    run_parser.add_argument("flow_name", help="Name of the flow to run")
    run_parser.add_argument("--params", "-p", help="JSON string or path to JSON file with parameters")
    run_parser.add_argument("--dry-run", action="store_true", help="Generate script but don't execute it")
    
    # Schedule subcommand
    schedule_parser = subparsers.add_parser("schedule", help="Manage flow schedules")
    schedule_subparsers = schedule_parser.add_subparsers(dest="schedule_command", help="Schedule command")
    
    # Schedule add command
    schedule_add_parser = schedule_subparsers.add_parser("add", help="Add a schedule for a flow")
    schedule_add_parser.add_argument("flow_name", help="Name of the flow to schedule")
    schedule_add_parser.add_argument("--interval", help="Schedule interval (hourly, daily, weekly, monthly)")
    schedule_add_parser.add_argument("--at", help="Time of day for daily/weekly/monthly schedules (HH:MM)")
    schedule_add_parser.add_argument("--cron", help="Custom cron expression")
    schedule_add_parser.add_argument("--description", help="Description of the schedule")
    schedule_add_parser.add_argument("--disabled", action="store_true", help="Add the schedule in disabled state")
    
    # Schedule remove command
    schedule_remove_parser = schedule_subparsers.add_parser("remove", help="Remove a flow schedule")
    schedule_remove_parser.add_argument("flow_name", help="Name of the flow to unschedule")
    
    # Schedule list command
    schedule_list_parser = schedule_subparsers.add_parser("list", help="List scheduled flows")
    
    # Scheduler daemon commands
    scheduler_parser = subparsers.add_parser("scheduler", help="Manage the scheduler daemon")
    scheduler_subparsers = scheduler_parser.add_subparsers(dest="scheduler_command", help="Scheduler command")
    
    # Start scheduler command
    scheduler_start_parser = scheduler_subparsers.add_parser("start", help="Start the scheduler daemon")
    scheduler_start_parser.add_argument("--foreground", "-f", action="store_true", help="Run in foreground (don't detach)")
    scheduler_start_parser.add_argument("--check-interval", type=int, default=60, help="How often to check schedules (seconds)")
    
    # Stop scheduler command
    scheduler_stop_parser = scheduler_subparsers.add_parser("stop", help="Stop the scheduler daemon")
    
    # Status scheduler command
    scheduler_status_parser = scheduler_subparsers.add_parser("status", help="Check scheduler daemon status")
    scheduler_status_parser.add_argument("--interactive", "-i", action="store_true", help="Show interactive dashboard")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Setup common arguments for scheduler
    scheduler_kwargs = {
        "flows_dir": args.flows_dir,
        "tasks_dir": args.tasks_dir,
        "output_dir": args.output_dir,
        "config_dir": args.config_dir,
        "log_dir": args.log_dir
    }
    
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
        if flows:
            table_header = f"{'FLOW NAME':<30} {'DESCRIPTION':<50}"
            print(f"\n{display.colorize(table_header, style='bold')}")
            print("-" * min(80, shutil.get_terminal_size().columns))
            
            for flow_name in flows:
                try:
                    # Try to load the flow to get description
                    flow_path = os.path.join(args.flows_dir, f"{flow_name}.json")
                    with open(flow_path, "r") as f:
                        flow_def = json.load(f)
                    
                    description = flow_def.get("description", "")
                    if len(description) > 50:
                        description = description[:47] + "..."
                    
                    print(f"{flow_name:<30} {description:<50}")
                except Exception:
                    print(f"{flow_name:<30} {'<Unable to load flow definition>':<50}")
    elif args.command == "run":
        params = {}
        if args.params:
            # Parse params as JSON string or file
            if args.params.startswith("{"):
                params = json.loads(args.params)
            else:
                with open(args.params, "r") as f:
                    params = json.load(f)
        
        # Show a nice output when running a flow
        flow_name = args.flow_name
        print(f"{display.colorize('⚙', 'blue')} Running flow: {display.colorize(flow_name, 'cyan', 'bold')}")
        
        start_time = datetime.datetime.now()
        
        try:
            script_path = featherflow.execute_flow(
                flow_name,
                params=params,
                dry_run=args.dry_run
            )
            
            end_time = datetime.datetime.now()
            duration = end_time - start_time
            
            print(f"\n{display.colorize('✓', 'green')} Flow completed successfully in {display.format_time_delta(duration)}")
            print(f"Script generated at: {script_path}")
        except Exception as e:
            end_time = datetime.datetime.now()
            duration = end_time - start_time
            
            print(f"\n{display.colorize('✗', 'red')} Flow failed after {display.format_time_delta(duration)}")
            print(f"Error: {str(e)}")
            sys.exit(1)
    elif args.command == "schedule":
        # Get the scheduler manager
        schedule_manager = scheduler.get_scheduler(**scheduler_kwargs).schedule_manager
        
        if args.schedule_command == "add":
            # Validate the flow exists
            flow_path = os.path.join(args.flows_dir, f"{args.flow_name}.json")
            if not os.path.exists(flow_path):
                print(f"Error: Flow {args.flow_name} not found in {args.flows_dir}")
                sys.exit(1)
            
            # Convert interval to cron if specified
            cron_expression = None
            if args.cron:
                cron_expression = args.cron
            elif args.interval:
                cron_expression = scheduler.interval_to_cron(args.interval, args.at)
            else:
                print("Error: Either --interval or --cron must be specified")
                sys.exit(1)
            
            # Add the schedule
            success = schedule_manager.add_schedule(
                args.flow_name,
                cron_expression,
                not args.disabled,
                args.description
            )
            
            if success:
                print(f"{display.colorize('✓', 'green')} Successfully scheduled flow {display.colorize(args.flow_name, 'cyan')}: {cron_expression}")
                
                # Calculate next run time
                schedule = schedule_manager.get_schedule(args.flow_name)
                if schedule and schedule.next_run:
                    print(f"Next run: {display.colorize(schedule.next_run.strftime('%Y-%m-%d %H:%M:%S'), 'yellow')}")
                
                # Check if scheduler is running
                scheduler_instance = scheduler.get_scheduler(**scheduler_kwargs)
                if not scheduler_instance.is_running():
                    print(f"\n{display.colorize('Note:', 'yellow')} Scheduler daemon is not running.")
                    print(f"Start it with: {display.colorize('featherflow scheduler start', 'blue')}")
            else:
                print(f"{display.colorize('✗', 'red')} Failed to schedule flow {args.flow_name}")
                sys.exit(1)
                
        elif args.schedule_command == "remove":
            success = schedule_manager.remove_schedule(args.flow_name)
            
            if success:
                print(f"{display.colorize('✓', 'green')} Successfully unscheduled flow {display.colorize(args.flow_name, 'cyan')}")
            else:
                print(f"{display.colorize('✗', 'red')} Failed to unschedule flow {args.flow_name}")
                sys.exit(1)
                
        elif args.schedule_command == "list":
            schedules = schedule_manager.get_all_schedules()
            
            if schedules:
                print(f"Found {display.colorize(str(len(schedules)), 'cyan')} scheduled flows:")
                
                # Create a table-like structure
                terminal_width = shutil.get_terminal_size().columns
                header = f"{'FLOW NAME':<20} {'SCHEDULE':<20} {'NEXT RUN':<25} {'STATUS':<10}"
                print(f"\n{display.colorize(header, style='bold')}")
                print("-" * min(len(header), terminal_width))
                
                # Sort by next run time
                upcoming = sorted(
                    [s for s in schedules if s.enabled and s.next_run],
                    key=lambda s: s.next_run
                ) + [s for s in schedules if not s.enabled or not s.next_run]
                
                for schedule in upcoming:
                    now = datetime.datetime.now()
                    next_run_str = schedule.next_run.strftime("%Y-%m-%d %H:%M:%S") if schedule.next_run else "N/A"
                    
                    # Format status with color
                    if schedule.running:
                        status = display.colorize("● Running", "green")
                    elif not schedule.enabled:
                        status = display.colorize("○ Disabled", "yellow")
                    elif schedule.next_run and (schedule.next_run - now).total_seconds() < 300:  # Next 5 minutes
                        status = display.colorize("○ Pending", "cyan")
                    else:
                        status = display.colorize("○ Scheduled", "blue")
                    
                    # Format row
                    flow_name = schedule.flow_name
                    if len(flow_name) > 20:
                        flow_name = flow_name[:17] + "..."
                    
                    cron_expr = schedule.cron_expression
                    if len(cron_expr) > 20:
                        cron_expr = cron_expr[:17] + "..."
                    
                    print(f"{flow_name:<20} {cron_expr:<20} {next_run_str:<25} {status}")
                    
                    if schedule.description:
                        print(f"  {display.colorize('Description:', 'blue')} {schedule.description}")
                
                # Check if scheduler is running
                scheduler_instance = scheduler.get_scheduler(**scheduler_kwargs)
                if not scheduler_instance.is_running():
                    print(f"\n{display.colorize('Note:', 'yellow')} Scheduler daemon is not running.")
                    print(f"Start it with: {display.colorize('featherflow scheduler start', 'blue')}")
            else:
                print("No scheduled flows found")
                
                # Show available flows as a helpful hint
                flows = featherflow.list_flows()
                if flows:
                    print(f"\nYou can schedule any of these flows:")
                    for flow in flows[:5]:  # Show up to 5 flows
                        print(f"  {flow}")
                    if len(flows) > 5:
                        print(f"  ... and {len(flows) - 5} more")
                    
                    print(f"\nExample: {display.colorize('featherflow schedule add example_flow --interval daily --at \"09:00\"', 'blue')}")
        else:
            schedule_parser.print_help()
            sys.exit(1)
    elif args.command == "scheduler":
        scheduler_instance = scheduler.get_scheduler(**scheduler_kwargs)
        
        if args.scheduler_command == "start":
            if args.check_interval:
                scheduler_instance.check_interval = args.check_interval
                
            if scheduler_instance.is_running():
                print(f"{display.colorize('!', 'yellow')} Scheduler is already running")
            else:
                if args.foreground:
                    print(f"{display.colorize('⚙', 'blue')} Starting scheduler in foreground mode...")
                    print("Press Ctrl+C to stop")
                    try:
                        scheduler.run_scheduler_daemon()
                    except KeyboardInterrupt:
                        print(f"\n{display.colorize('✓', 'green')} Scheduler stopped")
                else:
                    # Start in background
                    success = scheduler_instance.start()
                    if success:
                        print(f"{display.colorize('✓', 'green')} Scheduler started in background")
                        print(f"Use '{display.colorize('featherflow scheduler stop', 'blue')}' to stop the scheduler")
                        
                        # Keep the main process alive to prevent the thread from getting killed
                        # This is a simple approach - in production you'd use a proper daemon
                        print(f"\n{display.colorize('Press Ctrl+C to return to shell, scheduler will continue running', 'yellow')}")
                        try:
                            while True:
                                time.sleep(1)
                        except KeyboardInterrupt:
                            print(f"\n{display.colorize('Returning to shell (scheduler continues running in background)', 'green')}")
                    else:
                        print(f"{display.colorize('✗', 'red')} Failed to start scheduler")
                        sys.exit(1)
        elif args.scheduler_command == "stop":
            if not scheduler_instance.is_running():
                print(f"{display.colorize('!', 'yellow')} Scheduler is not running")
            else:
                success = scheduler_instance.stop()
                if success:
                    print(f"{display.colorize('✓', 'green')} Scheduler stopped")
                else:
                    print(f"{display.colorize('✗', 'red')} Failed to stop scheduler")
                    sys.exit(1)
        elif args.scheduler_command == "status":
            if args.interactive:
                # Show interactive dashboard
                display.dashboard_view(scheduler_instance)
            else:
                # Show static status information
                display.print_schedule_status(scheduler_instance)
        else:
            scheduler_parser.print_help()
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()