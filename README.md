# Secret Votes

a simple webserver for secret voting.

---

## Installation

Requires
* Python3

```$ python3 -m pip install -r requirements.txt ```

for production host e.g. as uwsgi socket

for debugging run a test server with 
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