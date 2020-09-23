import json
import random
from flask import Flask, request, render_template, redirect, url_for
import hashlib
from os import environ
import smtplib
import re
from flask_babel import Babel, _
from flask_bootstrap import Bootstrap

app = Flask(__name__)
Bootstrap(app)
babel = Babel(app)
LANGUAGES = ['en', 'de']

@app.route('/')
def root():
    # show homepage
    return render_template("homepage.html")

@app.route('/test')
def test():
    send_email("recipient@test.com","url","question?")
    return "test success at " + request.url_root + " with " + environ.get('SMTP_HOST') + " " + environ.get('SMTP_FROM')

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(LANGUAGES)

def store_poll(question, email_addresses):
    # create "unique" poll id
    poll_id = hashlib.sha256((question + "".join(email_addresses) + str(random.randint(1,999))).encode("utf-8")).hexdigest()[:16]
    # this poll might already exist, so seed with random number

    print("poll id", poll_id)

    # hash people for pseudonymisation
    people_hashed = [hashlib.sha256(p.encode("utf-8")).hexdigest()[:16] for p in email_addresses] # todo: move this to email sending, allow salt

    json_data = {"question" : question,
                "people_hashes" : random.sample(people_hashed, len(people_hashed)),
                "emails" : email_addresses,
                "num_yes" : 0,
                "num_no" : 0,
                "num_abstain" : 0,
                "already_voted" : [],
                "result_visible_time" : None}

    with open("data/poll_%s.json" % poll_id, "w", encoding="utf-8") as file:
        json.dump(json_data, file)
    
    return poll_id

@app.route('/submit_new_poll', methods=["POST","GET"])
def submit_poll():
    if request.method == 'POST':
        question = request.form.get('question', None)
        people = request.form.get('people', None)
    else:
        question = request.args.get("question",None)
        people = request.args.get("people",None)
    
    if not question or len(question.strip()) == 0:
        # empty motion field -> error msg and repeat
        return render_template("create_new_poll.html", invalid_question=True, question=question, people=people)

    print(question)
    if not people:
        # no emails provided -> error msg and repeat
        # todo: this splits question, when there is a space!
        return render_template("create_new_poll.html", invalid_mail=True, question=question, people=people)

    # strip whitespace from emails and split to list
    people_list = people.replace("\r","").strip().split("\n")

    # store data to server
    poll_id = store_poll(question, people_list)

    url = "%svote_%s" % (request.url_root, poll_id)
    if send_all_emails(people_list, url, question):
        return render_template("poll_created.html")
    else:
        # invalid emails provided -> error msg and repeat
        return render_template("create_new_poll.html", invalid_mail=True, question=question, people=people)

@app.route('/create', methods=["POST","GET"])
def create_poll():

    # show creation site
    return render_template("create_new_poll.html", people=_("Enter one email address per line..."))

@app.route('/vote_<poll_id>', methods=["POST","GET"])
def vote(poll_id):
    if request.method == 'POST':
        user_id = request.form.get('user', None)
    else:
        user_id = request.args.get("user", None)

    # get question
    try:
        with open("data/poll_%s.json" % poll_id) as file:
            vote_data = json.load(file)
            question = vote_data["question"]
    except FileNotFoundError as e:
        print(e)
        return render_template("error.html", error_type="invalid_poll_id")

    # check user allowed
    eligible_voters = vote_data["people_hashes"]
    if not user_id in eligible_voters:
        return render_template("error.html", error_type="invalid_user_id")

    return render_template("vote_poll.html", question=question, poll_id=poll_id, user=user_id)

@app.route("/submit_vote", methods=["POST","GET"])
def submit_vote():
    if request.method == 'POST':
        options = request.form.get('options', None)
        user_id = request.form.get('name', None)
        poll_id = request.form.get('poll_id', None)
    else:
        options = request.args.get("options", None)
        user_id = request.args.get("name", None)
        poll_id = request.args.get("poll_id", None)
    print(options,user_id, poll_id)

    # create results url
    url = "%sresult_%s?user=%s" % (request.url_root, poll_id, user_id)

    # todo: check invalid options

    # check if user is eligible for voting
    try:
        with open("data/poll_%s.json" % poll_id, encoding="utf-8") as file:
            vote_data = json.load(file)
    except FileNotFoundError as e:
        print(e)
        return render_template("error.html", error_type="invalid_poll_id")

    is_eligible = user_id in vote_data["people_hashes"]
    if not is_eligible:
        return render_template("error.html", error_type="invalid_user_id")

    # check if user has already voted
    if user_id in vote_data["already_voted"]:
        return render_template("error.html", error_type="already_voted", result_url=url)
    
    # add vote
    print(options)
    num_votes = vote_data["people_hashes"].count(user_id)
    vote_data["num_%s" % options] += num_votes

    # mark user as already voted
    vote_data["already_voted"].append(user_id)

    # store vote
    with open("data/poll_%s.json" % poll_id, "w", encoding="utf-8") as file:
        json.dump(vote_data,file)

    # show results
    return render_template("vote_submitted.html", result_url=url)

@app.route("/result_<poll_id>", methods=["GET","POST"])
def result(poll_id):
    if request.method == 'POST':
        user = request.form.get('user', None)
    else:
        user = request.args.get("user", None)

    # get data
    try:
        with open("data/poll_%s.json" % poll_id, encoding="utf-8") as file:
            vote_data = json.load(file)
    except FileNotFoundError as e:
        print(e)
        return render_template("error.html", error_type="invalid_poll_id")

    # only show results, when user has already voted
    if not user in vote_data["already_voted"]:
        return _("you can only see results if you have already voted!") # todo: return to vote

    motion = vote_data["question"]
    num_yes = vote_data["num_yes"]
    num_no = vote_data["num_no"]
    num_abstain = vote_data["num_abstain"]
    num_votes = num_abstain + num_no + num_yes
    num_missing = len(vote_data["people_hashes"]) - num_votes
    people = vote_data["emails"]
    people_num_votes = {}
    for p in people:
        people_num_votes[p] = people.count(p)
    print(people_num_votes)

    if num_missing < 0:
        print("something is fishy! more votes than registered voters!")

    return render_template("result_view_with_names.html", motion=motion, num_votes=num_votes, num_yes=num_yes, num_no=num_no, num_abstain=num_abstain, num_missing=num_missing, people=people_num_votes.items())

def send_all_emails(email_list, poll_url, question):
    # treat duplicate emails as double votes
    already_sent = set()

    for email in email_list:
        if len(email) == 0:
            # empty lines
            continue

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            # invalid email format
            return False

        if email in already_sent:
            continue
        
        send_email(email, poll_url, question, num_votes=email_list.count(email))
        already_sent.add(email)
    
    return True

def send_email(recipient, poll_url, question, num_votes=1):
    print("sending email")
    sender = environ.get('SMTP_FROM')
    receivers = [recipient]

    email_hash = hashlib.sha256((recipient).encode("utf-8")).hexdigest()[:16] # todo: this can be reconstructed, add salt 

    # todo: the language of the email is now the language of the poll creator -> determine from TLD?
    message = """From: Voting System <%s>\r\nTo: %s\r\nSubject: %s %s\r\n

    %s %s?user=%s
    %s %d %s.
    """ % (environ.get('SMTP_FROM'), recipient, _("You have been invited to participate to a poll regarding"), question, 
            _("\nClick here to submit your vote:\n\n"), poll_url, email_hash,
            _("\nYou have"), num_votes, _("vote(s)"))

    try:
        with smtplib.SMTP(environ.get('SMTP_HOST'), environ.get('SMTP_PORT')) as smtpObj:
            smtpObj.sendmail(sender, receivers, message.encode("utf-8"))
            print("Successfully sent email")
    except Exception as e:
        print("Error: unable to send email", e)

if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True)