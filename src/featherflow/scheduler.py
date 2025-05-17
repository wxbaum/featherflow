#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Scheduler functionality for Featherflow (without external dependencies)
"""

import os
import json
import time
import signal
import logging
import threading
import datetime
import re
from pathlib import Path
import subprocess
import atexit

from . import core

class SimpleSchedule:
    """Simple implementation of cron-like scheduling without external dependencies"""
    
    def __init__(self, cron_expression):
        """
        Initialize a simple schedule
        
        Args:
            cron_expression (str): Cron expression (minute hour day month weekday)
        """
        self.expression = cron_expression
        self.parts = self._parse_expression(cron_expression)
    
    def _parse_expression(self, expression):
        """Parse a cron expression into its components"""
        # Support for special strings
        if expression == "@hourly":
            expression = "0 * * * *"
        elif expression == "@daily":
            expression = "0 0 * * *"
        elif expression == "@weekly":
            expression = "0 0 * * 0"
        elif expression == "@monthly":
            expression = "0 0 1 * *"
        elif expression == "@yearly" or expression == "@annually":
            expression = "0 0 1 1 *"
        
        # Split the expression into parts
        parts = expression.strip().split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {expression}. Expected 5 parts.")
        
        # Parse each part
        result = []
        for i, part in enumerate(parts):
            # Determine allowed range for this position
            if i == 0:  # Minute
                allowed_range = range(0, 60)
            elif i == 1:  # Hour
                allowed_range = range(0, 24)
            elif i == 2:  # Day of month
                allowed_range = range(1, 32)
            elif i == 3:  # Month
                allowed_range = range(1, 13)
            elif i == 4:  # Day of week
                allowed_range = range(0, 7)  # 0 and 7 both represent Sunday
            
            # Parse the part
            if part == '*':
                result.append(list(allowed_range))
            elif '/' in part:  # Step values (*/2, */5)
                star, step = part.split('/')
                if star != '*':
                    raise ValueError(f"Invalid step format in {part}, only */step is supported")
                step = int(step)
                result.append([v for v in allowed_range if v % step == 0])
            elif ',' in part:  # Value list (1,3,5)
                values = [int(v) for v in part.split(',')]
                result.append(values)
            elif '-' in part:  # Range (1-5)
                start, end = part.split('-')
                result.append(list(range(int(start), int(end) + 1)))
            else:  # Single value
                result.append([int(part)])
        
        return result
    
    def matches(self, dt):
        """
        Check if the given datetime matches this schedule
        
        Args:
            dt (datetime.datetime): Datetime to check
            
        Returns:
            bool: True if the datetime matches, False otherwise
        """
        # Extract components from datetime
        minute = dt.minute
        hour = dt.hour
        day = dt.day
        month = dt.month
        weekday = dt.weekday()  # 0-6, where 0 is Monday
        
        # Adjust weekday to match cron format (0-6, where 0 is Sunday)
        weekday = (weekday + 1) % 7
        
        # Check if each component matches
        return (
            minute in self.parts[0] and
            hour in self.parts[1] and
            day in self.parts[2] and
            month in self.parts[3] and
            weekday in self.parts[4]
        )
    
    def get_next_occurrence(self, after=None):
        """
        Get the next occurrence of this schedule after the given datetime
        
        Args:
            after (datetime.datetime, optional): Datetime to start from (defaults to now)
            
        Returns:
            datetime.datetime: Next occurrence
        """
        if after is None:
            after = datetime.datetime.now()
        
        # Start checking from the next minute
        candidate = after.replace(second=0, microsecond=0) + datetime.timedelta(minutes=1)
        
        # Check candidates until we find a match
        # This is not efficient but works without external dependencies
        max_iterations = 24 * 60 * 31  # Check up to a month ahead (worst case)
        for _ in range(max_iterations):
            if self.matches(candidate):
                return candidate
            candidate += datetime.timedelta(minutes=1)
        
        # If we get here, something is wrong with the schedule
        raise ValueError(f"Could not find a match for schedule {self.expression} within a reasonable timeframe")


class ScheduleEntry:
    """Represents a scheduled flow"""
    
    def __init__(self, flow_name, cron_expression, enabled=True, description=None):
        """
        Initialize a schedule entry
        
        Args:
            flow_name (str): Name of the flow
            cron_expression (str): Cron expression for the schedule
            enabled (bool): Whether the schedule is active
            description (str, optional): Description of the schedule
        """
        self.flow_name = flow_name
        self.cron_expression = cron_expression
        self.enabled = enabled
        self.description = description
        self.last_run = None
        self.next_run = None
        self.running = False
        self.schedule = SimpleSchedule(cron_expression)
        
        # Initialize next run time
        self._calculate_next_run()
    
    def _calculate_next_run(self):
        """Calculate the next scheduled run time"""
        base_time = datetime.datetime.now()
        if self.last_run and self.last_run > base_time:
            base_time = self.last_run
            
        self.next_run = self.schedule.get_next_occurrence(base_time)
    
    def should_run(self):
        """Check if this flow should run now"""
        if not self.enabled:
            return False
            
        if self.running:
            return False
            
        now = datetime.datetime.now()
        return self.next_run <= now
    
    def mark_running(self):
        """Mark this flow as currently running"""
        self.running = True
        self.last_run = datetime.datetime.now()
    
    def mark_completed(self):
        """Mark this flow as completed"""
        self.running = False
        self._calculate_next_run()
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            "flow_name": self.flow_name,
            "cron_expression": self.cron_expression,
            "enabled": self.enabled,
            "description": self.description,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary"""
        schedule = cls(
            data["flow_name"],
            data["cron_expression"],
            data.get("enabled", True),
            data.get("description")
        )
        
        if data.get("last_run"):
            schedule.last_run = datetime.datetime.fromisoformat(data["last_run"])
            
        if data.get("next_run"):
            schedule.next_run = datetime.datetime.fromisoformat(data["next_run"])
            
        return schedule
    
    def __str__(self):
        status = "enabled" if self.enabled else "disabled"
        next_run = self.next_run.strftime("%Y-%m-%d %H:%M:%S") if self.next_run else "not scheduled"
        return f"{self.flow_name}: {self.cron_expression} ({status}) - next run: {next_run}"


class ScheduleManager:
    """Manages flow schedules"""
    
    def __init__(self, config_dir=None):
        """
        Initialize the schedule manager
        
        Args:
            config_dir (str, optional): Directory for schedule configuration
        """
        self.logger = logging.getLogger(__name__)
        
        # Set default config directory
        if config_dir is None:
            self.config_dir = os.path.expanduser("~/.featherflow")
        else:
            self.config_dir = config_dir
            
        os.makedirs(self.config_dir, exist_ok=True)
        
        self.schedule_file = os.path.join(self.config_dir, "schedules.json")
        self.schedules = {}
        
        # Load existing schedules
        self._load_schedules()
    
    def _load_schedules(self):
        """Load schedules from the configuration file"""
        if not os.path.exists(self.schedule_file):
            return
            
        try:
            with open(self.schedule_file, "r") as f:
                data = json.load(f)
                
            for schedule_data in data.get("schedules", []):
                schedule = ScheduleEntry.from_dict(schedule_data)
                self.schedules[schedule.flow_name] = schedule
                
            self.logger.info(f"Loaded {len(self.schedules)} schedules")
        except Exception as e:
            self.logger.error(f"Failed to load schedules: {str(e)}")
    
    def _save_schedules(self):
        """Save schedules to the configuration file"""
        try:
            schedules_data = {"schedules": []}
            
            for schedule in self.schedules.values():
                schedules_data["schedules"].append(schedule.to_dict())
                
            with open(self.schedule_file, "w") as f:
                json.dump(schedules_data, f, indent=2)
                
            self.logger.debug("Saved schedules")
        except Exception as e:
            self.logger.error(f"Failed to save schedules: {str(e)}")
    
    def add_schedule(self, flow_name, cron_expression, enabled=True, description=None):
        """
        Add a new schedule
        
        Args:
            flow_name (str): Name of the flow
            cron_expression (str): Cron expression for the schedule
            enabled (bool): Whether the schedule is active
            description (str, optional): Description of the schedule
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate the cron expression by creating a SimpleSchedule
            SimpleSchedule(cron_expression)
            
            schedule = ScheduleEntry(flow_name, cron_expression, enabled, description)
            self.schedules[flow_name] = schedule
            
            self._save_schedules()
            self.logger.info(f"Added schedule for flow {flow_name}: {cron_expression}")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to add schedule for flow {flow_name}: {str(e)}")
            return False
    
    def remove_schedule(self, flow_name):
        """
        Remove a schedule
        
        Args:
            flow_name (str): Name of the flow
            
        Returns:
            bool: True if successful, False otherwise
        """
        if flow_name in self.schedules:
            del self.schedules[flow_name]
            self._save_schedules()
            self.logger.info(f"Removed schedule for flow {flow_name}")
            return True
        else:
            self.logger.warning(f"No schedule found for flow {flow_name}")
            return False
    
    def get_schedule(self, flow_name):
        """Get a schedule by flow name"""
        return self.schedules.get(flow_name)
    
    def get_all_schedules(self):
        """Get all schedules"""
        return list(self.schedules.values())
    
    def get_due_schedules(self):
        """Get flows that are due to run"""
        due = []
        
        for schedule in self.schedules.values():
            if schedule.should_run():
                due.append(schedule)
                
        return due


class Scheduler:
    """Featherflow scheduler daemon"""
    
    def __init__(self, flows_dir="./flows", tasks_dir="./tasks", output_dir="./featherflow_output", 
                 config_dir=None, log_dir=None, check_interval=60):
        """
        Initialize the scheduler
        
        Args:
            flows_dir (str): Directory containing flow definitions
            tasks_dir (str): Directory containing task scripts
            output_dir (str): Directory for generated outputs
            config_dir (str, optional): Directory for configuration
            log_dir (str, optional): Directory for log files
            check_interval (int): How often to check schedules (seconds)
        """
        self.logger = logging.getLogger(__name__)
        
        self.flows_dir = flows_dir
        self.tasks_dir = tasks_dir
        self.output_dir = output_dir
        self.log_dir = log_dir
        self.check_interval = check_interval
        
        # Initialize schedule manager
        self.schedule_manager = ScheduleManager(config_dir)
        
        # Initialize Featherflow core
        self.featherflow = core.Featherflow(
            flows_dir=flows_dir,
            tasks_dir=tasks_dir,
            output_dir=output_dir
        )
        
        # Thread for running the scheduler
        self.scheduler_thread = None
        self.should_stop = threading.Event()
        
        # Track running flows
        self.running_flows = {}
    
    def start(self):
        """Start the scheduler daemon"""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.logger.warning("Scheduler is already running")
            return False
        
        # Create log directory if needed
        if self.log_dir:
            os.makedirs(self.log_dir, exist_ok=True)
        
        # Track start time for uptime calculation
        self._start_time = datetime.datetime.now()  # Add this line
        
        # Start the scheduler thread
        self.should_stop.clear()
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("Scheduler started")
        return True
    
    def stop(self):
        """Stop the scheduler daemon"""
        if not self.scheduler_thread or not self.scheduler_thread.is_alive():
            self.logger.warning("Scheduler is not running")
            return False
        
        self.logger.info("Stopping scheduler...")
        self.should_stop.set()
        self.scheduler_thread.join(timeout=30)
        
        if self.scheduler_thread.is_alive():
            self.logger.warning("Scheduler thread did not terminate cleanly")
            return False
        
        self.logger.info("Scheduler stopped")
        return True
    
    def is_running(self):
        """Check if the scheduler is running"""
        return self.scheduler_thread is not None and self.scheduler_thread.is_alive()
    
    def run_flow(self, flow_name, schedule=None):
        """
        Run a flow
        
        Args:
            flow_name (str): Name of the flow to run
            schedule (ScheduleEntry, optional): Schedule entry that triggered this run
        """
        try:
            # Mark the schedule as running if provided
            if schedule:
                schedule.mark_running()
            
            # Create a timestamp for the log file
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = None
            
            if self.log_dir:
                log_file = os.path.join(self.log_dir, f"{flow_name}_{timestamp}.log")
                # Create a log file directory if needed
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            # Start the flow in a separate thread
            flow_thread = threading.Thread(
                target=self._execute_flow,
                args=(flow_name, log_file, schedule)
            )
            flow_thread.daemon = True
            flow_thread.start()
            
            # Track the running flow
            self.running_flows[flow_name] = {
                "thread": flow_thread,
                "start_time": datetime.datetime.now(),
                "log_file": log_file,
                "schedule": schedule
            }
            
            self.logger.info(f"Started flow {flow_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to run flow {flow_name}: {str(e)}")
            if schedule:
                schedule.mark_completed()
            return False
    
    def _execute_flow(self, flow_name, log_file=None, schedule=None):
        """
        Execute a flow and handle logging
        
        Args:
            flow_name (str): Name of the flow to run
            log_file (str, optional): Path to log file
            schedule (ScheduleEntry, optional): Schedule entry that triggered this run
        """
        try:
            # Redirect stdout/stderr to log file if specified
            if log_file:
                with open(log_file, "w") as f:
                    # Save original stdout/stderr
                    original_stdout = os.dup(1)
                    original_stderr = os.dup(2)
                    
                    # Redirect stdout/stderr to log file
                    os.dup2(f.fileno(), 1)
                    os.dup2(f.fileno(), 2)
                    
                    try:
                        print(f"=== Starting flow {flow_name} at {datetime.datetime.now().isoformat()} ===")
                        # Execute the flow
                        script_path = self.featherflow.execute_flow(flow_name)
                        print(f"=== Flow {flow_name} completed at {datetime.datetime.now().isoformat()} ===")
                    finally:
                        # Restore original stdout/stderr
                        os.dup2(original_stdout, 1)
                        os.dup2(original_stderr, 2)
                        os.close(original_stdout)
                        os.close(original_stderr)
            else:
                # Execute the flow without redirecting output
                script_path = self.featherflow.execute_flow(flow_name)
        except Exception as e:
            self.logger.error(f"Error executing flow {flow_name}: {str(e)}")
        finally:
            # Clean up
            if flow_name in self.running_flows:
                del self.running_flows[flow_name]
            
            # Mark the schedule as completed if provided
            if schedule:
                schedule.mark_completed()
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        self.logger.info("Scheduler loop started")
        
        while not self.should_stop.is_set():
            try:
                # Get flows that are due to run
                due_schedules = self.schedule_manager.get_due_schedules()
                
                for schedule in due_schedules:
                    self.logger.info(f"Flow {schedule.flow_name} is due to run")
                    self.run_flow(schedule.flow_name, schedule)
                
                # Sleep until the next check
                self.should_stop.wait(self.check_interval)
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {str(e)}")
                # Sleep a bit to avoid tight loop on persistent errors
                time.sleep(5)
        
        self.logger.info("Scheduler loop stopped")


# Module-level singleton instance
_scheduler_instance = None

def get_scheduler(flows_dir="./flows", tasks_dir="./tasks", output_dir="./featherflow_output",
                 config_dir=None, log_dir=None, check_interval=60):
    """
    Get the singleton scheduler instance
    
    Args:
        flows_dir (str): Directory containing flow definitions
        tasks_dir (str): Directory containing task scripts
        output_dir (str): Directory for generated outputs
        config_dir (str, optional): Directory for configuration
        log_dir (str, optional): Directory for log files
        check_interval (int): How often to check schedules (seconds)
        
    Returns:
        Scheduler: Singleton scheduler instance
    """
    global _scheduler_instance
    
    if _scheduler_instance is None:
        _scheduler_instance = Scheduler(
            flows_dir=flows_dir,
            tasks_dir=tasks_dir,
            output_dir=output_dir,
            config_dir=config_dir,
            log_dir=log_dir,
            check_interval=check_interval
        )
    
    return _scheduler_instance

def interval_to_cron(interval, at=None):
    """
    Convert a human-readable interval to a cron expression
    
    Args:
        interval (str): Interval ('hourly', 'daily', 'weekly', 'monthly')
        at (str, optional): Time of day for daily/weekly/monthly (HH:MM)
        
    Returns:
        str: Equivalent cron expression
    """
    if interval.lower() == 'hourly':
        return "0 * * * *"  # At minute 0 of every hour
    
    if interval.lower() == 'daily':
        if at:
            hour, minute = at.split(':')
            return f"{minute} {hour} * * *"  # At specified time every day
        return "0 0 * * *"  # At midnight every day
    
    if interval.lower() == 'weekly':
        if at:
            hour, minute = at.split(':')
            return f"{minute} {hour} * * 0"  # At specified time every Sunday
        return "0 0 * * 0"  # At midnight every Sunday
    
    if interval.lower() == 'monthly':
        if at:
            hour, minute = at.split(':')
            return f"{minute} {hour} 1 * *"  # At specified time on the 1st of every month
        return "0 0 1 * *"  # At midnight on the 1st of every month
    
    # Default - return as is (assuming it's already a cron expression)
    return interval

def run_scheduler_daemon():
    """Run the scheduler as a daemon process"""
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print(f"Received signal {signum}, shutting down...")
        scheduler = get_scheduler()
        scheduler.stop()
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Register cleanup on exit
    def cleanup():
        scheduler = get_scheduler()
        if scheduler.is_running():
            scheduler.stop()
            
    atexit.register(cleanup)
    
    # Start the scheduler
    scheduler = get_scheduler()
    scheduler.start()
    
    # Keep the main thread alive
    while scheduler.is_running():
        try:
            # Sleep but also check for signals
            time.sleep(1)
        except KeyboardInterrupt:
            break
    
    print("Scheduler daemon shutting down")