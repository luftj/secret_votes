# Secret Votes

a simple webserver for secret voting.

---

## Features

* sends emails via SMTP to invite all users to vote!
* Full localisation. To add a new language, run `pybabel init -i messages.pot -d app/translations -l <iso-code>`, edit the new .pot file in `app/translations/<iso_code>/LC_MESSAGES/messages.po` and create a [pull request](https://github.com/luftj/secret_votes/compare)!

## Installation

Requires
* Python3
* flask
* flask-babel
* (docker)

set environment variables:
* SMTP_HOST location (IP or DN) of SMTP server
* SMTP_PORT port of SMTP server
* SMTP_FROM e-mail address to send from

### production
host e.g. as uwsgi socket, see [flask docs](https://flask.palletsprojects.com/en/1.1.x/deploying/uwsgi/).

Alternatively, you can run the application inside a docker container with the handy script `./start.sh`. Might want to change the port from 8080 to something that is available on your machine.

### debugging
install with
`$ python3 -m pip install -r requirements.txt`
and run a test server with 
`$ python3 main.py`

run a test mail server, e.g. [MailHog](https://github.com/mailhog/MailHog) with `docker run -p 8026:8025 -p 1026:1025 mailhog/mailhog`

## Usage

To create a poll:
`http://localhost:5000/create`

the people's names that are eligible for voting must be seperated with a new line.

To vote:
`http://localhost:5000/vote_<poll_id>?user=<user_id>`

The name you enter must exactly match one of the names entered before to authenticate you.

To see the results:
`http://localhost:5000/result_<poll_id>?user=<user_id>`

You are only allowed to see the results, after you have given a vote.

## To do
* block result viewing for specific time or until number of votes reached
* salt email hashes so they can't be found from email alone
* set language of email by looking at tld
* add observers that can view results without voting
* possibility to change the possible answers for the vote
* add option to create form, whether to list emails in plain text in result
* download bootstrap/etc with container creation, don't leak user data to twitter cdn
* option for vote end time
* send email to poll creater, when voting is done
* put meta (disclaimer, etc) links in cfg or something
* favicon
* write some tests :)