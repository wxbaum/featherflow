# Featherflow

An ultra-lightweight workflow orchestration tool built with Python's standard library. Featherflow is designed to be a simple alternative to Apache Airflow for smaller projects or when you need a lightweight solution without the infrastructure overhead. 

As an example, Featherflow will happily run on the smallest EC2 instance AWS offers, t2.nano.  

## Features

- **JSON-based Flow Definitions**: Define workflows using simple JSON files
- **Task Dependencies**: Specify dependencies between tasks for proper execution order
- **Bash Script Generation**: Automatically generates bash scripts to execute your workflows
- **Minimal Dependencies**: Uses only Python standard library - no external dependencies required
- **Command Line Interface**: Easy to use CLI for running and managing workflows
- **Temp Directory Management**: Automatically creates and cleans up temporary directories

## Why I Made Featherflow

Modern workflow orchestration tools like Apache Airflow, Prefect, and Luigi provide powerful features but come with:

- Heavy installation footprints
- Complex infrastructure requirements 
- Steep learning curves
- Dependency conflicts
- Overkill for simpler workflow needs

I wanted a minimalist approach that could run on the cheapest possible servers and micro computers like Raspberry Pi, so I created Featherflow.

## Installation

```bash
# Install from PyPI
pip install featherflow

# Or directly from source
git clone https://github.com/wxbaum/featherflow.git
cd featherflow
pip install .
```

## Quick Start

### 1. Create a Flow Definition

Create a JSON file that defines your workflow:

```json
{
  "name": "simple_flow",
  "description": "A sample flow to demonstrate Featherflow",
  "tasks": [
    {
      "id": "fetch_data",
      "script": "fetch_data.py",
      "description": "Fetch data from source"
    },
    {
      "id": "process_data",
      "script": "process_data.py",
      "description": "Process the fetched data",
      "depends_on": ["fetch_data"],
      "args": {
        "input-file": "data/raw_data.csv",
        "output-file": "data/processed_data.csv"
      }
    },
    {
      "id": "generate_report",
      "script": "generate_report.py",
      "description": "Generate final report",
      "depends_on": ["process_data"],
      "args": ["--format", "json", "--output", "reports/final_report.json"]
    }
  ]
}
```
Save your flow as <flow_name> in a folder named flows. 

### 2. Create Task Scripts

Create Python scripts for each task in your workflow. Tasks should:
- Be standalone Python scripts
- Accept command-line arguments as needed
- Return 0 for success, non-zero for failure

Example task script:

```python
#!/usr/bin/env python3
import sys
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Fetch data")
    # Add any arguments your task needs
    args, _ = parser.parse_known_args()  # Use known_args to handle Featherflow's argument passing
    return args

def main():
    args = parse_args()
    print("Fetching data...")
    # Your data fetching code here
    
    # Access the temporary directory if needed
    import os
    tmp_dir = os.environ.get('TMP_DIR', os.path.join(os.getcwd(), 'tmp'))
    # Do something with tmp_dir...
    
    return 0  # Return 0 for success

if __name__ == "__main__":
    sys.exit(main())
```

Save your tasks in a folder named tasks. The tasks folder should be parallel to flows. 

### 3. Run Your Flow

From the root folder containing flows and tasks, use the Featherflow CLI to execute your workflow:

```bash
# List available flows
featherflow list

# Run a flow
featherflow run simple_flow

# Run with parameters
featherflow run simple_flow --params '{"date": "2023-01-01", "source": "example"}'

# Generate script without executing (dry run)
featherflow run simple_flow --dry-run
```

## Flow Definition Reference

A Featherflow flow is defined in a JSON file with the following structure:

```json
{
  "name": "flow_name",
  "description": "Flow description",
  "version": "1.0",
  "tasks": [
    {
      "id": "task_id",
      "script": "script_filename.py",
      "description": "Task description",
      "depends_on": ["other_task_id"],
      "args": ["--arg1", "value1"],
      "env": {
        "ENV_VAR1": "value1"
      }
    }
  ]
}
```

### Top-level Fields

- `name` (required): Name of the flow
- `description`: Description of the flow
- `version`: Version of the flow
- `tasks` (required): Array of task definitions

### Task Fields

- `id` (required): Unique identifier for the task
- `script` (required): Python script to execute
- `description`: Description of the task
- `depends_on`: List of task IDs that must complete before this task runs
- `args`: Command line arguments (array or object)
- `env`: Environment variables for this task

## CLI Reference

```
featherflow --flows-dir FLOWS_DIR --tasks-dir TASKS_DIR [command] [options]
```

### Global Options

- `--flows-dir`, `-f`: Directory containing flow JSON files (default: ./flows)
- `--tasks-dir`, `-t`: Directory containing task scripts (default: ./tasks)
- `--output-dir`, `-o`: Directory for generated bash scripts and logs (default: ./featherflow_output)
- `--log-level`, `-l`: Logging level (default: INFO)

### Commands

#### List Flows

```
featherflow list
```

Lists all available flows in the flows directory.

#### Run Flow

```
featherflow run FLOW_NAME [options]
```

Executes the specified flow.

Options:
- `--params`, `-p`: JSON string or path to JSON file with parameters
- `--dry-run`: Generate script but don't execute it

## How Featherflow Works

Featherflow operates with a simple execution model:

1. **Parse Flow Definition**: Reads and validates your JSON flow definition
2. **Resolve Dependencies**: Determines the correct order of task execution
3. **Generate Bash Script**: Creates a bash script that will run your tasks in order
4. **Create Temp Directory**: Sets up a temporary workspace for task execution
5. **Execute Tasks**: Runs each task script with appropriate arguments
6. **Check Status**: Monitors and reports task completion status
7. **Clean Up**: Removes the temporary directory when the flow completes

This approach allows Featherflow to be lightweight and portable, while still providing essential workflow orchestration capabilities.

## Example: Weather Observation Flow

Here's a complete example of a workflow that:
1. Fetches weather data from multiple stations
2. Aggregates the data into a CSV file
3. Generates a readable synopsis

### Flow Definition

```json
{
  "name": "weather_observations_flow",
  "description": "Collect, aggregate and report weather observations",
  "tasks": [
    {
      "id": "get_lax_obs",
      "script": "get_observations.py",
      "args": {
        "station": "KLAX"
      }
    },
    {
      "id": "get_sfo_obs",
      "script": "get_observations.py",
      "args": {
        "station": "KSFO"
      }
    },
    {
      "id": "get_nyc_obs",
      "script": "get_observations.py",
      "args": {
        "station": "KNYC"
      }
    },
    {
      "id": "aggregate_data",
      "script": "aggregate_data_to_csv.py",
      "depends_on": ["get_lax_obs", "get_sfo_obs", "get_nyc_obs"],
      "args": {
        "output": "weather_data.csv"
      }
    },
    {
      "id": "generate_synopsis",
      "script": "generate_synopsis.py",
      "depends_on": ["aggregate_data"],
      "args": {
        "input": "weather_data.csv",
        "format": "fancy"
      }
    }
  ]
}
```

This creates a simple but powerful DAG:

```
get_lax_obs ─┐
             │
get_sfo_obs ─┼─→ aggregate_data → generate_synopsis
             │
get_nyc_obs ─┘
```

See the examples directory for full implementations of these task scripts.

## Best Practices

### Task Design

1. **Idempotent Tasks**: Design tasks that can be safely run multiple times
2. **Clean Error Handling**: Return appropriate exit codes and log errors
3. **Parameterize**: Use command-line arguments rather than hardcoding values
4. **Use the Temp Directory**: Store intermediate files in the TMP_DIR environment variable
5. **Parse Arguments Safely**: Use `parser.parse_known_args()` instead of `parse_args()`

### Flow Structure

1. **Meaningful Task IDs**: Use descriptive IDs that indicate what the task does
2. **Granular Tasks**: Break complex operations into smaller, focused tasks
3. **Dependency Chain**: Explicitly declare all dependencies between tasks
4. **Environment Variables**: Use env section for configuration rather than hardcoding

## Python API

You can also use Featherflow programmatically in your Python code:

```python
from featherflow import Featherflow

# Initialize Featherflow
featherflow = Featherflow(
    flows_dir="./flows",
    tasks_dir="./tasks",
    output_dir="./featherflow_output"
)

# List available flows
flows = featherflow.list_flows()
print(f"Available flows: {flows}")

# Execute a flow
script_path = featherflow.execute_flow(
    "sample_flow",
    params={"date": "2023-01-01"},
    dry_run=False
)
```

## Contributing

Contributions are welcome! As a lightweight tool, Featherflow aims to remain simple and dependency-free. Please consider these guidelines when contributing:

1. **Standard Library Only**: Avoid adding external dependencies
2. **Backward Compatibility**: Ensure changes work with Python 3.7+
3. **Test Coverage**: Include tests for new features or bug fixes
4. **Documentation**: Update docs to reflect changes

## License

GPL-3.0 License
