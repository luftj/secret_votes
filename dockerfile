FROM tiangolo/uwsgi-nginx-flask:python3.8

#Install Cron
RUN apt-get update
RUN apt-get -y install cron

# Copy cron file to the cron.d directory
COPY cronjobs /etc/cron.d/cronjobs

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/cronjobs

# Apply cron job
RUN crontab /etc/cron.d/cronjobs

# Create the log file
RUN touch /app/cron.log

# expose SMTP port
EXPOSE 587

# install python requirements
COPY ./requirements.txt /app/requirements.txt
RUN python -m pip install -r /app/requirements.txt

# moce application data
COPY ./app/ /app

# give exec rights to delete script in cronjob
RUN chmod 0744 /app/delete_old_polls.sh