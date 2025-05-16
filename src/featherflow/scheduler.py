#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Scheduler functionality for Featherflow
"""

import os
import json
import logging
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
import shutil

def generate_crontab_entry(flow_name, cron_expression, flows_dir, tasks_dir, output_dir, log_file=None):
    """
    Generate a crontab entry for a flow
    
    Args:
        flow_name (str): Name of the flow to schedule
        cron_expression (str): Cron expression for the schedule
        flows_dir (str): Directory containing flow definitions
        tasks_dir (str): Directory containing task scripts
        output_dir (str): Directory for generated outputs
        log_file (str, optional): Path to log file
        
    Returns:
        str: Crontab entry line
    """
    # Get the full path to the featherflow executable
    featherflow_bin = shutil.which('featherflow')
    if not featherflow_bin:
        # Fallback to using python -m featherflow
        featherflow_cmd = f"python -m featherflow"
    else:
        featherflow_cmd = featherflow_bin
    
    # Build the cron command
    cmd = (f"{cron_expression} {featherflow_cmd} "
           f"--flows-dir {flows_dir} "
           f"--tasks-dir {tasks_dir} "
           f"--output-dir {output_dir} "
           f"run {flow_name}")
    
    # Add output redirection if log file specified
    if log_file:
        cmd += f" >> {log_file} 2>&1"
    
    return cmd

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

def get_current_crontab():
    """
    Get the current user's crontab content
    
    Returns:
        str: Current crontab content
    """
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout
        # Some systems return exit code 1 if no crontab exists
        return ""
    except Exception as e:
        logging.error(f"Failed to get current crontab: {str(e)}")
        return ""

def update_crontab(crontab_content):
    """
    Update the user's crontab
    
    Args:
        crontab_content (str): New crontab content
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Write crontab content to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write(crontab_content)
            temp_path = temp_file.name
        
        # Install the new crontab
        result = subprocess.run(['crontab', temp_path], capture_output=True, text=True)
        
        # Clean up the temporary file
        os.unlink(temp_path)
        
        if result.returncode == 0:
            return True
        else:
            logging.error(f"Failed to update crontab: {result.stderr}")
            return False
    except Exception as e:
        logging.error(f"Error updating crontab: {str(e)}")
        return False

def add_flow_schedule(flow_name, schedule, flows_dir, tasks_dir, output_dir, log_dir=None):
    """
    Add a schedule for a flow to the crontab
    
    Args:
        flow_name (str): Name of the flow to schedule
        schedule (dict): Schedule specification
        flows_dir (str): Directory containing flow definitions
        tasks_dir (str): Directory containing task scripts
        output_dir (str): Directory for generated outputs
        log_dir (str, optional): Directory for log files
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    # Convert schedule to cron expression if needed
    if 'expression' in schedule:
        cron_expression = schedule['expression']
    elif 'interval' in schedule:
        cron_expression = interval_to_cron(schedule['interval'], schedule.get('at'))
    else:
        logger.error(f"Invalid schedule for flow {flow_name}: {schedule}")
        return False
    
    # Setup log file if log_dir is specified
    log_file = None
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f"{flow_name}_{timestamp}.log")
    
    # Generate the crontab entry
    entry = generate_crontab_entry(
        flow_name, cron_expression, flows_dir, tasks_dir, output_dir, log_file
    )
    
    # Add a comment to identify this entry
    crontab_entry = f"# Featherflow scheduled flow: {flow_name}\n{entry}\n"
    
    # Get the current crontab
    current_crontab = get_current_crontab()
    
    # Check if this flow is already scheduled
    flow_comment = f"# Featherflow scheduled flow: {flow_name}"
    if flow_comment in current_crontab:
        # Remove existing schedule for this flow
        lines = current_crontab.split('\n')
        new_lines = []
        skip_next = False
        
        for line in lines:
            if flow_comment in line:
                skip_next = True
                continue
            if skip_next:
                skip_next = False
                continue
            new_lines.append(line)
        
        current_crontab = '\n'.join(new_lines)
    
    # Add the new schedule
    new_crontab = current_crontab + crontab_entry
    
    # Update the crontab
    success = update_crontab(new_crontab)
    if success:
        logger.info(f"Successfully scheduled flow {flow_name}")
    
    return success

def remove_flow_schedule(flow_name):
    """
    Remove a flow's schedule from the crontab
    
    Args:
        flow_name (str): Name of the flow to unschedule
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    # Get the current crontab
    current_crontab = get_current_crontab()
    
    # Check if this flow is scheduled
    flow_comment = f"# Featherflow scheduled flow: {flow_name}"
    if flow_comment not in current_crontab:
        logger.warning(f"Flow {flow_name} is not currently scheduled")
        return True
    
    # Remove the schedule
    lines = current_crontab.split('\n')
    new_lines = []
    skip_next = False
    
    for line in lines:
        if flow_comment in line:
            skip_next = True
            continue
        if skip_next:
            skip_next = False
            continue
        new_lines.append(line)
    
    new_crontab = '\n'.join(new_lines)
    
    # Update the crontab
    success = update_crontab(new_crontab)
    if success:
        logger.info(f"Successfully unscheduled flow {flow_name}")
    
    return success

def list_scheduled_flows():
    """
    List all scheduled flows from the crontab
    
    Returns:
        list: List of dictionaries with flow names and schedules
    """
    # Get the current crontab
    current_crontab = get_current_crontab()
    
    # Find all Featherflow scheduled flows
    scheduled_flows = []
    lines = current_crontab.split('\n')
    
    for i, line in enumerate(lines):
        if "# Featherflow scheduled flow:" in line and i < len(lines) - 1:
            flow_name = line.split(':')[1].strip()
            cron_parts = lines[i+1].split()[:5]  # Get the cron timing parts
            cron_expression = ' '.join(cron_parts)
            
            scheduled_flows.append({
                'flow_name': flow_name,
                'cron_expression': cron_expression,
                'full_command': lines[i+1]
            })
    
    return scheduled_flows