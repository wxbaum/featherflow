import yaml

def generate_bash_from_dag(dag):
    bash_script = ["#!/bin/bash"]
    
    for tasks in dag:
        if isinstance(tasks, list):
            for task in tasks:
                bash_script.append(f"./{task} &")
        else:
            bash_script.append(f"./{tasks}")
    
        bash_script.append("wait")
    
    return "\n".join(bash_script)

with open("dag.yaml", 'r') as file:
    data = yaml.safe_load(file)
    bash_script_content = generate_bash_from_dag(data['dag'])

with open("dag_executor.sh", 'w') as file:
    file.write(bash_script_content)
