import os
import yaml
import argparse

def find_python_files(directory):
    """Finds all Python files in the given directory."""
    return sorted([f for f in os.listdir(directory) if f.endswith(".py")])

def load_dependencies(yaml_file):
    """Loads task dependencies from a YAML file."""
    if not yaml_file:
        return {}
    try:
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
            return data.get('tasks', {})
    except FileNotFoundError:
        print(f"Warning: Dependency file '{yaml_file}' not found.")
        return {}
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file '{yaml_file}': {e}")
        return {}

def generate_bash_script(python_files, dependencies, output_file):
    """Generates a bash script to run Python files based on dependencies."""
    bash_commands = "#!/bin/bash\n\n"
    executed_tasks = set()

    # Handle tasks with no dependencies first
    for task, dep_info in dependencies.items():
        if not dep_info.get('dependencies'):
            python_file = f"{task}.py"
            if python_file in python_files and task not in executed_tasks:
                bash_commands += f"echo \"Executing {python_file}\"\n"
                bash_commands += f"python {python_file}\n"
                bash_commands += "if [ $? -ne 0 ]; then\n"
                bash_commands += f"  echo \"Error executing {python_file}, exiting.\"\n"
                bash_commands += "  exit 1\n"
                bash_commands += "fi\n\n"
                executed_tasks.add(task)

    # Handle tasks with dependencies
    while len(executed_tasks) < len(dependencies):
        found_new_task = False
        for task, dep_info in dependencies.items():
            if task not in executed_tasks:
                ready_to_execute = True
                for dep in dep_info.get('dependencies', []):
                    if dep not in executed_tasks:
                        ready_to_execute = False
                        break
                if ready_to_execute:
                    python_file = f"{task}.py"
                    if python_file in python_files:
                        bash_commands += f"echo \"Executing {python_file}\"\n"
                        bash_commands += f"python {python_file}\n"
                        bash_commands += "if [ $? -ne 0 ]; then\n"
                        bash_commands += f"  echo \"Error executing {python_file}, exiting.\"\n"
                        bash_commands += "  exit 1\n"
                        bash_commands += "fi\n\n"
                        executed_tasks.add(task)
                        found_new_task = True
        if not found_new_task and len(executed_tasks) < len(dependencies):
            unexecuted = [task for task in dependencies if task not in executed_tasks]
            print(f"Warning: Potential circular or unresolved dependencies. Unexecuted tasks: {unexecuted}")
            break # Avoid infinite loop

    # Execute any remaining python files without explicit dependencies
    for py_file in python_files:
        task_name = py_file[:-3]
        if task_name not in dependencies:
            bash_commands += f"echo \"Executing {py_file} (no explicit dependency)\"\n"
            bash_commands += f"python {py_file}\n"
            bash_commands += "if [ $? -ne 0 ]; then\n"
            bash_commands += f"  echo \"Error executing {py_file}, exiting.\"\n"
            bash_commands += "  exit 1\n"
            bash_commands += "fi\n\n"

    with open(output_file, 'w') as f:
        f.write(bash_commands)

    print(f"Bash script '{output_file}' generated successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generates a bash script to run Python files based on dependencies.")
    parser.add_argument("python_dir", help="Directory containing the Python files.")
    parser.add_argument("-d", "--dependencies", help="Path to the YAML file defining dependencies (optional).")
    parser.add_argument("-o", "--output", default="run_workflow.sh", help="Name of the output bash script (default: run_workflow.sh).")

    args = parser.parse_args()

    python_files = find_python_files(args.python_dir)
    dependencies = load_dependencies(args.dependencies)

    # Ensure all dependency tasks have corresponding python files
    defined_tasks = set(dependencies.keys())
    available_tasks = {f[:-3] for f in python_files}
    for task in defined_tasks:
        if task not in available_tasks:
            print(f"Warning: Task '{task}' defined in dependencies but '{task}.py' not found.")

    generate_bash_script(python_files, dependencies, args.output)