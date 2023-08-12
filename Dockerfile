FROM python:3.11-slim-buster

# Install cron and required dependencies
RUN apt-get update && apt-get -y install cron gcc libyaml-dev

# Copy DAG definition, python script, and requirements
COPY dag.yaml /app/dag.yaml
COPY generate_bash.py /app/generate_bash.py
COPY requirements.txt /app/requirements.txt

# Copy startup, config, and task files into /app 
COPY config/* /app/
COPY startup/* /app/
COPY tasks/* /app/

# Set work directory
WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Generate bash script from DAG
RUN python startup/generate_executor_bash_script.py

# Grant execute permission to the generated script and all task scripts
RUN chmod +x dag_executor.sh

# Set up cron job, e.g., to run every hour
RUN echo "* * * * * /app/dag_execution.sh" | crontab -

# Run cron in foreground
CMD ["cron", "-f"]
