#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility functions for Featherflow
"""

import os
import logging

def validate_path(path, create=False, is_dir=False):
    """
    Validate that a path exists and is accessible
    
    Args:
        path (str): Path to validate
        create (bool): Whether to create the path if it doesn't exist
        is_dir (bool): Whether the path should be a directory
        
    Returns:
        bool: True if the path is valid, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    if os.path.exists(path):
        if is_dir and not os.path.isdir(path):
            logger.error(f"Path exists but is not a directory: {path}")
            return False
        elif not is_dir and not os.path.isfile(path):
            logger.error(f"Path exists but is not a file: {path}")
            return False
        
        return True
    elif create:
        try:
            if is_dir:
                os.makedirs(path, exist_ok=True)
                logger.info(f"Created directory: {path}")
            else:
                # Create parent directory if needed
                parent_dir = os.path.dirname(path)
                if parent_dir and not os.path.exists(parent_dir):
                    os.makedirs(parent_dir, exist_ok=True)
                    logger.info(f"Created parent directory: {parent_dir}")
                
                # Create empty file
                with open(path, "w") as f:
                    pass
                logger.info(f"Created file: {path}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to create path {path}: {str(e)}")
            return False
    else:
        logger.error(f"Path does not exist: {path}")
        return False

def get_file_contents(file_path):
    """
    Read the contents of a file
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: Contents of the file, or None if the file doesn't exist
    """
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, "r") as f:
        return f.read()

def write_file_contents(file_path, contents):
    """
    Write contents to a file
    
    Args:
        file_path (str): Path to the file
        contents (str): Contents to write
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create parent directory if needed
        parent_dir = os.path.dirname(file_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        
        with open(file_path, "w") as f:
            f.write(contents)
        
        return True
    except Exception as e:
        logger.error(f"Failed to write to file {file_path}: {str(e)}")
        return False