# Featherflow

An ultra-lightweight workflow orchestration tool built with Python's standard library. Featherflow is designed to be a simple alternative to Apache Airflow for smaller projects or when you need a lightweight solution without the infrastructure overhead.

As an example, Featherflow will happily run on the smallest EC2 instance AWS offers: t2.nano.

![GitHub License](https://img.shields.io/github/license/wxbaum/featherflow)
![Python Versions](https://img.shields.io/badge/python-3.7%2B-blue)

## Features

- **Zero External Dependencies**: Built entirely with Python's standard library
- **JSON-based Flow Definitions**: Define workflows using simple JSON files
- **Task Dependencies**: Specify dependencies between tasks for proper execution order
- **Bash Script Generation**: Automatically generates bash scripts to execute your workflows
- **CLI Interface**: Easy-to-use command line tool for running and managing workflows
- **Built-in Scheduler**: Schedule workflows to run on intervals without external cron
- **Temp Directory Management**: Automatically creates and cleans up temporary directories
- **Interactive Dashboard**: Monitor running flows with a terminal-based dashboard

## Why Featherflow Exists

Modern workflow orchestration tools like Apache Airflow, Prefect, and Luigi provide powerful features but come with:

- Heavy installation footprints
- Complex infrastructure requirements 
- Steep learning curves
- Dependency conflicts
- Overkill for simpler workflow needs

Featherflow was created as a minimalist approach that can run on the cheapest possible servers and micro computers like Raspberry Pi.

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

Create a JSON file in a directory named `flows` with a structure like this:

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

Save this file as `simple_flow.json` in the `flows` directory.

### 2. Create Task Scripts

Create Python scripts for each task in a directory named `tasks`:

```python
#!/usr/bin/env python3
import sys
import argparse
import os

def parse_args():
    parser = argparse.ArgumentParser(description="Fetch data")
    # Add any arguments your task needs
    args, _ = parser.parse_known_args()  # Use known_args to handle Featherflow's argument passing
    return args

def main():
    args = parse_args()
    print("Fetching data...")
    
    # Access the temporary directory if needed
    tmp_dir = os.environ.get('TMP_DIR', os.path.join(os.getcwd(), 'tmp'))
    # You can create files in the temp directory that other tasks can use
    with open(f"{tmp_dir}/fetched_data.txt", "w") as f:
        f.write("Example data")
    
    return 0  # Return 0 for success

if __name__ == "__main__":
    sys.exit(main())
```

Save this as `fetch_data.py` in the `tasks` directory, and create similar scripts for your other tasks.

### 3. Run Your Flow

Use the Featherflow CLI to execute your workflow:

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

## Project Structure

A typical Featherflow project looks like this:

```
my_project/
├── flows/
│   ├── simple_flow.json
│   └── another_flow.json
├── tasks/
│   ├── fetch_data.py
│   ├── process_data.py
│   └── generate_report.py
└── featherflow_output/  # Generated automatically
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
- `args`: Command line arguments (array or object format)
- `env`: Environment variables for this task

## Command Line Interface

The Featherflow CLI provides these commands:

```
featherflow [global-options] COMMAND [command-options]
```

### Global Options

- `--flows-dir`, `-f`: Directory containing flow JSON files (default: ./flows)
- `--tasks-dir`, `-t`: Directory containing task scripts (default: ./tasks)
- `--output-dir`, `-o`: Directory for generated bash scripts and logs (default: ./featherflow_output)
- `--log-level`, `-l`: Logging level (default: INFO)
- `--log-dir`: Directory for log files (optional)
- `--config-dir`: Directory for configuration files (optional, default: ~/.featherflow)

### Commands

#### List Flows

```bash
featherflow list
```

Lists all available flows in the flows directory.

#### Run Flow

```bash
featherflow run FLOW_NAME [options]
```

Options:
- `--params`, `-p`: JSON string or path to JSON file with parameters
- `--dry-run`: Generate script but don't execute it

#### Schedule Management

```bash
# Add a schedule
featherflow schedule add FLOW_NAME --interval daily --at "03:00"

# List all schedules
featherflow schedule list

# Remove a schedule
featherflow schedule remove FLOW_NAME
```

Options for `schedule add`:
- `--interval`: Human-readable interval (hourly, daily, weekly, monthly)
- `--at`: Time of day for daily/weekly/monthly schedules (HH:MM)
- `--cron`: Custom cron expression (e.g., "*/5 * * * *" for every 5 minutes)
- `--description`: Optional description of the schedule
- `--disabled`: Add the schedule in disabled state

#### Scheduler Daemon Management

```bash
# Start the scheduler
featherflow scheduler start [--foreground] [--check-interval 60]

# Check scheduler status
featherflow scheduler status [--interactive]

# Stop the scheduler
featherflow scheduler stop
```

Options for `scheduler start`:
- `--foreground`, `-f`: Run in foreground (don't detach)
- `--check-interval`: How often to check schedules in seconds (default: 60)

Options for `scheduler status`:
- `--interactive`, `-i`: Show interactive dashboard

## Scheduling Examples

```bash
# Run a flow hourly
featherflow schedule add data_sync_flow --interval hourly

# Run a flow daily at 3:00 AM
featherflow schedule add nightly_report_flow --interval daily --at "03:00"

# Run a flow weekly on Sunday at 9:00 AM
featherflow schedule add weekly_summary_flow --interval weekly --at "09:00"

# Run a flow monthly on the 1st at midnight
featherflow schedule add monthly_report_flow --interval monthly

# Run a flow every 15 minutes using cron syntax
featherflow schedule add monitoring_flow --cron "*/15 * * * *"

# Run a flow at specific times using cron
featherflow schedule add business_hours_flow --cron "0 9-17 * * 1-5" --description "Every hour during business hours, weekdays only"
```

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

For scheduler access:

```python
from featherflow import scheduler

# Get the scheduler instance
scheduler_instance = scheduler.get_scheduler(
    flows_dir="./flows",
    tasks_dir="./tasks",
    output_dir="./output",
    check_interval=60
)

# Start the scheduler
scheduler_instance.start()

# Add a schedule
schedule_manager = scheduler_instance.schedule_manager
schedule_manager.add_schedule(
    "sample_flow",
    "0 * * * *",  # Run hourly
    enabled=True,
    description="Hourly processing"
)

# Stop the scheduler
scheduler_instance.stop()
```

## How Featherflow Works

Featherflow operates with a simple execution model:

1. **Parse Flow Definition**: Reads and validates your JSON flow definition
2. **Resolve Dependencies**: Determines the correct order of task execution
3. **Generate Bash Script**: Creates a bash script that will run your tasks in order
4. **Create Temp Directory**: Sets up a temporary workspace for task execution
5. **Execute Tasks**: Runs each task script with appropriate arguments
6. **Check Status**: Monitors and reports task completion status
7. **Clean Up**: Removes the temporary directory when the flow completes

## Example Weather Observation Flow

The weather observation flow included in the examples demonstrates a real-world usage pattern:

```
get_lax_obs ─┐
             │
get_sfo_obs ─┼─→ aggregate_data → generate_synopsis
             │
get_nyc_obs ─┘
```

This flow:
1. Fetches weather data from three different weather stations (LAX, SFO, NYC)
2. Aggregates all the data into a single CSV file
3. Generates a readable weather synopsis report

To run this example:
```bash
featherflow run weather_observations_flow
```

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

## Contributing

Contributions are welcome! As a lightweight tool, Featherflow aims to remain simple and dependency-free. Please consider these guidelines when contributing:

1. **Standard Library Only**: Avoid adding external dependencies
2. **Backward Compatibility**: Ensure changes work with Python 3.7+
3. **Test Coverage**: Include tests for new features or bug fixes
4. **Documentation**: Update docs to reflect changes

## License

GPL-3.0 License
