#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Core functionality for Featherflow
"""
import os
import json
import logging
from . import executor
from . import parser
from . import utils

class Featherflow:
    """Main class for Featherflow workflow orchestration"""
    def __init__(self, flows_dir="./flows", tasks_dir="./tasks", output_dir="./featherflow_output", log_level=None):
        """Initialize Featherflow"""
        self.flows_dir = flows_dir
        self.tasks_dir = tasks_dir
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)
        
        # Set log level if provided
        if log_level:
            self.logger.setLevel(getattr(logging, log_level.upper()))
            
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
    def list_flows(self):
        """List all available flows in the flows directory"""
        self.logger.info(f"Listing flows in {self.flows_dir}")
        flows = []
        if os.path.exists(self.flows_dir):
            for file in os.listdir(self.flows_dir):
                if file.endswith(".json"):
                    flows.append(file.replace(".json", ""))
        return flows
        
    def execute_flow(self, flow_name, params=None, dry_run=False):
        """Execute a flow with the given name"""
        self.logger.info(f"Executing flow {flow_name}")
        # Load flow definition
        flow_path = os.path.join(self.flows_dir, f"{flow_name}.json")
        if not os.path.exists(flow_path):
            self.logger.error(f"Flow definition not found: {flow_path}")
            raise FileNotFoundError(f"Flow definition not found: {flow_path}")
            
        with open(flow_path, "r") as f:
            flow_def = json.load(f)
            
        # Parse flow definition
        flow = parser.parse_flow(flow_def, params or {})
        
        # Generate bash script
        script_path = executor.generate_script(
            flow,
            self.tasks_dir,
            self.output_dir
        )
        
        # Execute the script unless dry_run is True
        if not dry_run:
            executor.execute_script(script_path)
        return script_path