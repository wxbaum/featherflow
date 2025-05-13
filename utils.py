"""
Utility functions for Featherflow
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def load_json_file(file_path: str) -> Dict:
    """
    Load and parse a JSON file
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Parsed JSON as a dictionary
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        raise ValueError(f"Invalid JSON in {file_path}: {e}")
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

def save_json_file(data: Dict, file_path: str) -> None:
    """
    Save data to a JSON file
    
    Args:
        data: Data to save
        file_path: Path to save the JSON file
    """
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {e}")
        raise

def get_task_full_path(task_name: str, tasks_dir: str) -> str:
    """
    Get the full path to a task script
    
    Args:
        task_name: Name of the task script (with or without extension)
        tasks_dir: Directory containing task scripts
        
    Returns:
        Full path to the task script
    """
    tasks_dir_path = Path(tasks_dir)
    
    # Check if task_name already has an extension
    if '.' in task_name:
        task_path = tasks_dir_path / task_name
        if task_path.exists():
            return str(task_path)
    
    # Try with .py extension
    task_path = tasks_dir_path / f"{task_name}.py"
    if task_path.exists():
        return str(task_path)
    
    # Try with .sh extension
    task_path = tasks_dir_path / f"{task_name}.sh"
    if task_path.exists():
        return str(task_path)
    
    # If not found, return original path which will cause an error later
    logger.warning(f"Task script not found: {task_name}")
    return str(tasks_dir_path / task_name)

def get_env_var(name: str, default: Optional[Any] = None) -> Any:
    """
    Get an environment variable, with optional JSON parsing
    
    Args:
        name: Name of the environment variable
        default: Default value if not found
        
    Returns:
        Value of the environment variable, parsed as JSON if applicable
    """
    value = os.environ.get(name)
    
    if value is None:
        return default
    
    # Try to parse as JSON
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        # Return as string if not valid JSON
        return value