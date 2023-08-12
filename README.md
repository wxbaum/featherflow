# Featherflow

Welcome to Featherflow! 

This is a lightweight task-scheduling tool designed for use with Docker. Multiple tasks with dependencies on one another can be chained together to create DAGs. If you're familiar with AirFlow, this tool is much the same concept, just in a significantly more lightweight package. 

If you're not familiar with DAGs, Astronomer has a good [introduction](https://www.astronomer.io/blog/what-exactly-is-a-dag/#:~:text=A%20DAG%20is%20a%20Directed,represent%20an%20almost%20identical%20mechanism). 

If you're looking for a highly scalable solution with rich features, [Airflow](https://airflow.apache.org/) is a better option. If you only need a basic tool, or one without the same RAM and CPU overhead, keep reading. 

## Project Structure
 * [Dockerfile](./Dockerfile)
 * [README.md](./README.md)
 * [dag.yaml](./dag.yaml)
 * [dag_executor.sh](./dag_executor.sh)
 * [generate_executor_bash_script.py](./generate_executor_bash_script.py)
 * [requirements.txt](./requirements.txt)
 * [config](./config)
   * [supported_commands.yaml](./config/supported_commands.yaml)
 * [tasks](./tasks)
   * [task1.sh](./tasks/task1.sh)
   * [task2a.sh](./tasks/task2a.sh)
   * [task2b.sh](./tasks/task2b.sh)
   * [task3.sh](./tasks/task3.sh)

## Setup & Installation
docker build -t featherflow .

## Run the Container
docker run featherflow

## Usage
Define your DAG: Edit the dag.yaml to define the sequence and parallelism 
of tasks.
Add Task Scripts: Place your task shell scripts in the /tasks directory.
Generate Executor Script: Run the generate_executor_bash_script.py to 
produce dag_executor.sh.
Execute the DAG: Run the dag_executor.sh script to start the execution of 
your tasks.

## Contributions
If you'd like to contribute to Featherflow, please fork the repository, 
make your changes, and submit a pull request. We value your feedback and 
contributions!

