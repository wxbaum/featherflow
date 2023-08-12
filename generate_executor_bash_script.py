"""
This Python script generates a bash script according to the contents and
structure of dag.yaml, and the contents of /tasks. 
"""

import yaml
from pathlib import Path

def generate_bash_from_dag(dag):
    """
    Generate a bash script to execute tasks based on the structure of the provided DAG.
    
    The DAG structure can have tasks listed sequentially or in parallel. If tasks are
    in a list, they are executed in parallel; otherwise, they're executed sequentially.
    
    Parameters:
    - dag (list): A list representing the DAG structure, where each item can either be
                  a string (task name) or a list of strings (parallel tasks).
    
    Returns:
    - str: Bash script content.
    """
    # Open supported commands and create lookup dict
    supported_commands_filepath = r'./config/supported_commands.yaml'
    commands = yaml.safe_load(Path(supported_commands_filepath).read_text())

    bash_script = ["#!/bin/bash"]
    
    # Iterate over tasks in the DAG
    for tasks in dag:
        # If the current tasks are a list, they are to be run in parallel
        if isinstance(tasks, list):
            for task in tasks:
                # Get the file type then lookup the shell command to 
                #   insert into the bash script
                file_extention = task.split('.')[-1]
                command = commands[file_extention]
                bash_script.append(f"{command} ./tasks/{task} &")
        # If the current task is a single item, it's run sequentially
        else:
            file_extention = tasks.split('.')[-1]
            command = commands[file_extention]
            bash_script.append(f"sh ./tasks/{tasks}")
        
        # Wait for parallel tasks to complete before proceeding
        bash_script.append("wait")
    
    return "\n".join(bash_script)


# Load the DAG structure from the yaml file
with open("dag.yaml", "r") as file:
    data = yaml.safe_load(file)
    bash_script_content = generate_bash_from_dag(data["dag"])

# Write the generated bash script to a file
with open("dag_executor.sh", "w") as file:
    file.write(bash_script_content)
