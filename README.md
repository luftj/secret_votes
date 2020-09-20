# Secret Votes

a simple webserver for secret voting.

---

## Installation

Requires
* Python3
* (docker)

For production, host e.g. as uwsgi socket, see [flask docs](https://flask.palletsprojects.com/en/1.1.x/deploying/uwsgi/).

Alternatively, you can run the application inside a docker container with the handy script `./start.sh`. Might want to change the port from 8080 to something that is available on your machine.

For debugging, install with
`$ python3 -m pip install -r requirements.txt`
and run a test server with 
`$ python3 main.py`

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

## Features

* sends emails via SMTP to invite all users to vote!
* Full localisation. To add a new language, run `pybabel init -i messages.pot -d app/translations -l <iso-code>`, edit the new .pot file in `app/translations/<iso_code>/LC_MESSAGES/messages.po` and create a pull request!

## To do
* prettier front end
* block result viewing for specific time or until number of votes reached
* salt email hashes so they can't be found from email alone
* set language of email by looking at tld
* add observers, that can view results without voting
* possibility to change the possible answers for the vote