# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy crontab file to the cron.d directory
COPY crontab /etc/cron.d/jira_cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/jira_cron

# Apply cron job
RUN crontab /etc/cron.d/jira_cron

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Run the command on container startup
CMD cron && tail -f /var/log/cron.log
