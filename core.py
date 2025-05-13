"""
Core Featherflow implementation
"""
import json
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Union

from .parser import parse_flow
from .executor import generate_bash_script

logger = logging.getLogger(__name__)

class Featherflow:
    """
    Main Featherflow class for orchestrating lightweight workflows
    """
    def __init__(
        self, 
        flows_dir: str, 
        tasks_dir: str,
        output_dir: Optional[str] = None,
        log_level: str = "INFO"
    ):
        """
        Initialize Featherflow
        
        Args:
            flows_dir: Directory containing flow JSON files
            tasks_dir: Directory containing Python task scripts
            output_dir: Directory for generated bash scripts and logs (default: ./featherflow_output)
            log_level: Logging level (default: INFO)
        """
        self.flows_dir = Path(flows_dir)
        self.tasks_dir = Path(tasks_dir)
        self.output_dir = Path(output_dir) if output_dir else Path("./featherflow_output")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set up logging
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.output_dir / "featherflow.log")
            ]
        )
        
        logger.info(f"Featherflow initialized with flows_dir={flows_dir}, tasks_dir={tasks_dir}")
        
        # Validate directories
        if not self.flows_dir.exists():
            raise ValueError(f"Flows directory does not exist: {flows_dir}")
        if not self.tasks_dir.exists():
            raise ValueError(f"Tasks directory does not exist: {tasks_dir}")
    
    def list_flows(self) -> List[str]:
        """List all available flow files"""
        return [f.name for f in self.flows_dir.glob("*.json")]
    
    def load_flow(self, flow_name: str) -> Dict:
        """
        Load a flow from a JSON file
        
        Args:
            flow_name: Name of the flow file (with or without .json extension)
        
        Returns:
            Flow definition as a dictionary
        """
        # Add .json extension if not present
        if not flow_name.endswith(".json"):
            flow_name = f"{flow_name}.json"
            
        flow_path = self.flows_dir / flow_name
        
        if not flow_path.exists():
            raise ValueError(f"Flow file does not exist: {flow_path}")
        
        with open(flow_path, "r") as f:
            flow_def = json.load(f)
            
        logger.info(f"Loaded flow: {flow_name}")
        return flow_def
    
    def execute_flow(
        self, 
        flow_name: str,
        params: Optional[Dict] = None,
        dry_run: bool = False
    ) -> str:
        """
        Execute a flow by generating and running a bash script
        
        Args:
            flow_name: Name of the flow to execute
            params: Parameters to pass to the flow (optional)
            dry_run: If True, generate the script but don't execute it
            
        Returns:
            Path to the generated bash script
        """
        # Load and parse the flow
        flow_def = self.load_flow(flow_name)
        parsed_flow = parse_flow(flow_def)
        
        # Generate timestamp for the run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        script_name = f"{flow_name.replace('.json', '')}_{timestamp}.sh"
        script_path = self.output_dir / script_name
        
        # Generate bash script
        script_content = generate_bash_script(
            parsed_flow, 
            self.tasks_dir,
            params=params
        )
        
        # Write bash script to file
        with open(script_path, "w") as f:
            f.write(script_content)
        
        # Make script executable
        os.chmod(script_path, 0o755)
        
        logger.info(f"Generated bash script: {script_path}")
        
        if not dry_run:
            # Execute the script
            logger.info(f"Executing flow: {flow_name}")
            os.system(f"bash {script_path}")
            logger.info(f"Completed flow: {flow_name}")
        else:
            logger.info(f"Dry run - script not executed: {script_path}")
        
        return str(script_path)