# MiniFlow

A ultra-lightweight workflow orchestration tool built with Python's standard library. MiniFlow is designed to be a simple alternative to Apache Airflow for smaller projects or when you need a lightweight solution without the infrastructure overhead.

## Features

- **JSON-based Flow Definitions**: Define workflows using simple JSON files
- **Task Dependencies**: Specify dependencies between tasks for proper execution order
- **Bash Script Generation**: Automatically generates bash scripts to execute your workflows
- **Minimal Dependencies**: Uses only Python standard library
- **Command Line Interface**: Easy to use CLI for running and managing workflows

## Installation

```bash
# Install from source
git clone https://github.com/yourusername/miniflow.git
cd miniflow
pip install .

# Or directly from PyPI (when published)
# pip install miniflow
```

## Quick Start

### 1. Create a Flow Definition

Create a JSON file that defines your workflow:

```json
{
  "name": "sample_flow",
  "description": "A sample flow to demonstrate MiniFlow",
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

### 2. Create Task Scripts

Create Python scripts for each task in your workflow:

```python
# fetch_data.py
import sys
print("Fetching data...")
# Your data fetching code here
sys.exit(0)
```

### 3. Run Your Flow

Use the MiniFlow CLI to execute your workflow:

```bash
# List available flows
miniflow list

# Run a flow
miniflow run sample_flow

# Run with parameters
miniflow run sample_flow --params '{"date": "2023-01-01", "source": "example"}'

# Generate script without executing (dry run)
miniflow run sample_flow --dry-run
```

## Flow Definition Reference

A MiniFlow flow is defined in a JSON file with the following structure:

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
miniflow --flows-dir FLOWS_DIR --tasks-dir TASKS_DIR [command] [options]
```

### Global Options

- `--flows-dir`, `-f`: Directory containing flow JSON files (default: ./flows)
- `--tasks-dir`, `-t`: Directory containing task scripts (default: ./tasks)
- `--output-dir`, `-o`: Directory for generated bash scripts and logs (default: ./miniflow_output)
- `--log-level`, `-l`: Logging level (default: INFO)

### Commands

#### List Flows

```
miniflow list
```

Lists all available flows in the flows directory.

#### Run Flow

```
miniflow run FLOW_NAME [options]
```

Executes the specified flow.

Options:
- `--params`, `-p`: JSON string or path to JSON file with parameters
- `--dry-run`: Generate script but don't execute it

## Python API

You can also use MiniFlow programmatically in your Python code:

```python
from miniflow import MiniFlow

# Initialize MiniFlow
miniflow = MiniFlow(
    flows_dir="./flows",
    tasks_dir="./tasks",
    output_dir="./miniflow_output"
)

# List available flows
flows = miniflow.list_flows()
print(f"Available flows: {flows}")

# Execute a flow
script_path = miniflow.execute_flow(
    "sample_flow",
    params={"date": "2023-01-01"},
    dry_run=False
)
```

## License

MIT License