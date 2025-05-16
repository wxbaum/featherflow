#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Executor functionality for Featherflow
"""

import os
import subprocess
import logging
import datetime
import shutil
from . import utils

def generate_script(flow, tasks_dir, output_dir):
    """
    Generate a bash script to execute a flow
    
    Args:
        flow (dict): Parsed flow definition
        tasks_dir (str): Directory containing task scripts
        output_dir (str): Directory to output generated scripts
        
    Returns:
        str: Path to the generated bash script
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Generating script for flow: {flow['name']}")
    
    # Create a timestamp for unique script naming
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    script_filename = f"{flow['name']}_{timestamp}.sh"
    script_path = os.path.join(output_dir, script_filename)
    
    # Get task execution order based on dependencies
    task_order = get_task_execution_order(flow["tasks"])
    logger.info(f"Task execution order: {task_order}")
    
    # Generate script content
    script_content = generate_script_content(flow, task_order, tasks_dir)
    
    # CRITICAL FIX: Directly modify the script content to ensure TEMP_DIR is defined
    # This is a more direct approach to ensure the variable is defined regardless of template
    if "TEMP_DIR=" not in script_content:
        # Add TEMP_DIR definition after the shebang and before the rest of the script
        temp_dir_def = """
# Create absolute path for temp directory
TEMP_DIR="$PWD/tmp"
echo "Creating temporary directory at: $TEMP_DIR"
mkdir -p "$TEMP_DIR"
if [ ! -d "$TEMP_DIR" ]; then
    echo "Error: Failed to create temporary directory: $TEMP_DIR"
    exit 1
fi
"""
        script_lines = script_content.split('\n')
        # Insert after the first line (shebang) and any comment lines at the top
        insert_index = 1
        while insert_index < len(script_lines) and (script_lines[insert_index].strip().startswith('#') or not script_lines[insert_index].strip()):
            insert_index += 1
        
        script_lines.insert(insert_index, temp_dir_def)
        script_content = '\n'.join(script_lines)
    
    # Ensure cleanup happens using trap to handle errors and normal exits
    if "trap" not in script_content:
        cleanup_trap = """
# Setup cleanup trap to ensure tmp directory is removed even on errors
trap 'echo "Cleaning up temporary directory"; rm -rf "$TEMP_DIR"; echo "Cleanup complete"' EXIT
"""
        # Insert after TEMP_DIR definition
        temp_dir_end = script_content.find('fi', script_content.find('TEMP_DIR='))
        if temp_dir_end > 0:
            temp_dir_end += 2  # Move past the 'fi'
            script_content = script_content[:temp_dir_end] + cleanup_trap + script_content[temp_dir_end:]
    
    # Remove any existing cleanup code at the end that might be conflicting
    if "# Clean up temp directory if flow completes successfully" in script_content:
        cleanup_start = script_content.find("# Clean up temp directory if flow completes successfully")
        cleanup_end = script_content.find("\necho \"Flow completed successfully", cleanup_start)
        if cleanup_end > 0:
            script_content = script_content[:cleanup_start] + script_content[cleanup_end:]
    
    # Write script to file
    with open(script_path, "w") as f:
        f.write(script_content)
    
    # Make the script executable
    os.chmod(script_path, 0o755)
    
    logger.info(f"Script generated at: {script_path}")
    return script_path

def execute_script(script_path):
    """
    Execute a generated bash script
    
    Args:
        script_path (str): Path to the bash script to execute
        
    Returns:
        int: Return code from the script execution
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Executing script: {script_path}")
    
    # Execute the script
    process = subprocess.Popen(
        script_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        shell=True
    )
    
    # Stream output in real-time
    for line in process.stdout:
        logger.info(line.strip())
    
    # Wait for the process to complete
    process.wait()
    
    # Check for errors
    if process.returncode != 0:
        for line in process.stderr:
            logger.error(line.strip())
        logger.error(f"Script execution failed with return code: {process.returncode}")
    else:
        logger.info("Script execution completed successfully")
    
    return process.returncode

def get_task_execution_order(tasks):
    """
    Determine the order in which tasks should be executed based on dependencies
    
    Args:
        tasks (list): List of task definitions
        
    Returns:
        list: List of task IDs in execution order
    """
    # Build a dependency graph
    task_ids = [task["id"] for task in tasks]
    dependencies = {task["id"]: task.get("depends_on", []) for task in tasks}
    
    # Check for missing dependencies
    for task_id, deps in dependencies.items():
        for dep in deps:
            if dep not in task_ids:
                raise ValueError(f"Task {task_id} depends on non-existent task: {dep}")
    
    # Topological sort to get execution order
    visited = set()
    temp_visited = set()
    order = []
    
    def visit(task_id):
        if task_id in temp_visited:
            raise ValueError(f"Circular dependency detected involving task: {task_id}")
        
        if task_id not in visited:
            temp_visited.add(task_id)
            
            for dep in dependencies[task_id]:
                visit(dep)
                
            temp_visited.remove(task_id)
            visited.add(task_id)
            order.append(task_id)
    
    for task_id in task_ids:
        if task_id not in visited:
            visit(task_id)
    
    return order

def generate_script_content(flow, task_order, tasks_dir):
    """
    Generate the content of the bash script
    
    Args:
        flow (dict): Flow definition
        task_order (list): Order in which tasks should be executed
        tasks_dir (str): Directory containing task scripts
        
    Returns:
        str: Content of the bash script
    """
    # Get the bash script template
    template_path = os.path.join(os.path.dirname(__file__), "templates", "bash_template.sh")
    
    if os.path.exists(template_path):
        with open(template_path, "r") as f:
            template = f.read()
    else:
        # Fallback to a basic template with trap for cleanup
        template = """#!/bin/bash

# Featherflow generated script for flow: {flow_name}
# Generated on: {datetime}

set -e  # Exit on any error

# Create absolute path for temp directory
TEMP_DIR="$PWD/tmp"
echo "Creating temporary directory at: $TEMP_DIR"
mkdir -p "$TEMP_DIR"
if [ ! -d "$TEMP_DIR" ]; then
    echo "Error: Failed to create temporary directory: $TEMP_DIR"
    exit 1
fi

# Setup cleanup trap to ensure tmp directory is removed even on errors
trap 'echo "Cleaning up temporary directory"; rm -rf "$TEMP_DIR"; echo "Cleanup complete"' EXIT

echo "Starting flow: {flow_name}"

{task_commands}

echo "Flow completed successfully: {flow_name}"
"""
    
    # Generate task commands
    task_commands = []
    task_map = {task["id"]: task for task in flow["tasks"]}
    
    for task_id in task_order:
        task = task_map[task_id]
        script_path = os.path.join(tasks_dir, task["script"])
        command = f"python {script_path}"
        
        # Add arguments if specified
        if "args" in task:
            if isinstance(task["args"], list):
                command += " " + " ".join(task["args"])
            elif isinstance(task["args"], dict):
                for key, value in task["args"].items():
                    if len(key) == 1:
                        command += f" -{key} {value}"
                    else:
                        command += f" --{key}={value}"
        
        # Add environment variables if specified
        env_vars = ""
        if "env" in task:
            for key, value in task["env"].items():
                env_vars += f"{key}={value} "
            command = f"{env_vars}{command}"
        
        # Set TMP_DIR environment variable for all tasks
        command = f"TMP_DIR=\"$TEMP_DIR\" {command}"
        
        # Build the dependency check code
        dependency_checks = ""
        if "depends_on" in task and task["depends_on"]:
            dependency_checks = "# Check dependencies\n"
            for dep_id in task["depends_on"]:
                dependency_checks += f"""echo "Checking dependency {dep_id} for task {task_id}"
while ! [[ -f "$TEMP_DIR/{dep_id}.status" && "$(cat $TEMP_DIR/{dep_id}.status)" == "0" ]]; do
    echo "Waiting for dependency {dep_id} to complete..."
    sleep 5
done
"""
        
        # Complete task command with dependency checks and status reporting
        task_cmd = f"""echo 'Running task: {task_id}'
{dependency_checks}{command}
task_status=$?
echo "[FEATHERFLOW_STATUS] Task {task_id} completed with status $task_status"
echo "$task_status" > "$TEMP_DIR/{task_id}.status"
if [[ $task_status -ne 0 ]]; then
    echo "Task {task_id} failed with status $task_status"
    exit $task_status
fi"""
        
        task_commands.append(task_cmd)
    
    # Fill in the template
    script_content = template.format(
        flow_name=flow["name"],
        datetime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        task_commands="\n\n".join(task_commands)
    )
    
    return script_content