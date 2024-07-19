# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install cron
RUN apt-get update && apt-get -y install cron

# Add crontab file in the cron directory
COPY crontab /etc/cron.d/ranking-cron

# Ensure the crontab file has a newline at the end
RUN sed -i '$a\' /etc/cron.d/ranking-cron

# Give execution rights on the cron job and the daily update script
RUN chmod 0644 /etc/cron.d/ranking-cron
RUN chmod +x /app/daily_update.py

# Apply cron job
RUN crontab /etc/cron.d/ranking-cron

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Create a startup script
RUN echo '#!/bin/bash\ncron\nstreamlit run app.py' > /app/start.sh
RUN chmod +x /app/start.sh

# Run the startup script
CMD ["/app/start.sh"]