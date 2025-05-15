#!/bin/bash

# Featherflow generated script for flow: {flow_name}
# Generated on: {datetime}

set -e  # Exit on any error

echo "Starting flow: {flow_name}"
{task_commands}
echo "Flow completed successfully: {flow_name}"