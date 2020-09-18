FROM tiangolo/uwsgi-nginx-flask:python3.8

#Install Cron
RUN apt-get update
RUN apt-get -y install cron

COPY . /app

# give exec rights to delete script in cronjob
RUN chmod 0744 /app/delete_old_polls.sh

# Copy cron file to the cron.d directory
COPY cronjobs /etc/cron.d/cronjobs

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/cronjobs

# Apply cron job
RUN crontab /etc/cron.d/cronjobs

# Create the log file
RUN touch /var/log/cron.log