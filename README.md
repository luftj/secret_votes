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
`http://localhost:5000/vote_<poll_id>`

The name you enter must exactly match one of the names entered before to authenticate you.

To see the results:
`http://localhost:5000/result_<poll_id>`

## To do
* localisation
* prettier front end
* block result viewing for specific time or until number of votes reached
* cryptographically hide names, so they can't be matched to hashes by the server admin
* salt email hashes so they can't be found from email alone