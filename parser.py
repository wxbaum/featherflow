#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Parser functionality for Featherflow
"""

import logging

def parse_flow(flow_def, params=None):
    """
    Parse a flow definition and apply parameters
    
    Args:
        flow_def (dict): Flow definition loaded from JSON
        params (dict): Optional parameters to apply to the flow definition
        
    Returns:
        dict: Parsed flow definition with parameters applied
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Parsing flow: {flow_def.get('name', 'unnamed')}")
    
    # Apply parameters to the flow definition
    if params:
        logger.info(f"Applying parameters: {params}")
        flow_def = apply_params(flow_def, params)
    
    # Validate the flow definition
    validate_flow(flow_def)
    
    return flow_def

def apply_params(flow_def, params):
    """
    Apply parameters to a flow definition
    
    Args:
        flow_def (dict): Flow definition
        params (dict): Parameters to apply
        
    Returns:
        dict: Flow definition with parameters applied
    """
    # Make a copy of the flow definition to avoid modifying the original
    import copy
    flow_def = copy.deepcopy(flow_def)
    
    # TODO: Implement parameter substitution logic
    # This could involve replacing placeholders in the flow definition
    # with values from the params dict
    
    return flow_def

def validate_flow(flow_def):
    """
    Validate that a flow definition is well-formed
    
    Args:
        flow_def (dict): Flow definition to validate
        
    Raises:
        ValueError: If the flow definition is invalid
    """
    logger = logging.getLogger(__name__)
    
    # Check required fields
    if "name" not in flow_def:
        logger.error("Flow definition missing required field: name")
        raise ValueError("Flow definition missing required field: name")
    
    if "tasks" not in flow_def or not isinstance(flow_def["tasks"], list):
        logger.error("Flow definition must contain a list of tasks")
        raise ValueError("Flow definition must contain a list of tasks")
    
    # Check that all tasks have required fields
    for i, task in enumerate(flow_def["tasks"]):
        if "id" not in task:
            logger.error(f"Task {i} is missing required field: id")
            raise ValueError(f"Task {i} is missing required field: id")
        
        if "script" not in task:
            logger.error(f"Task {task['id']} is missing required field: script")
            raise ValueError(f"Task {task['id']} is missing required field: script")