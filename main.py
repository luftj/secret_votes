import json
import random
from flask import Flask, request, render_template, redirect, url_for
import hashlib
from os import environ 
import smtplib
import re

app = Flask(__name__)


@app.route('/')
def root():
    return redirect(url_for('create_poll'))

@app.route('/test')
def test():
    send_email("recipient@test.com","url","question?")
    return "test success at " + request.url_root + " with " + environ.get('SMTP_HOST') + " " + environ.get('SMTP_FROM')

def store_poll(question, people):
    # create "unique" poll id
    poll_id = hashlib.md5((question+"".join(people)).encode("utf-8")).hexdigest()
    print("poll id", poll_id)

    # hash people for pseudonymisation
    people_hashed = [hashlib.md5(p.encode("utf-8")).hexdigest() for p in people]

    json_data = {"question" : question,
                "people_hashes" : random.sample(people_hashed, len(people_hashed)),
                "people_names" : people,
                "num_yes" : 0,
                "num_no" : 0,
                "num_abstain" : 0,
                "already_voted" : [],
                "result_visible_time" : None}

    with open("data/poll_%s.json" % poll_id,"w",encoding="utf-8") as file:
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
    # todo: handle invalid/None
    # todo: handle empty
    print(question)
    people_list = people.replace("\r","").split("\n")
    print(people_list)

    poll_id = store_poll(question, people_list)
    url = "%svote_%s" % (request.url_root, poll_id)

    if send_all_emails(people_list, url, question):
        return render_template("poll_created.html")
    else:
        return render_template("create_new_poll.html", invalid_mail=True, question=question, people=people)


@app.route('/create', methods=["POST","GET"])
def create_poll():
    # show creation site
    return render_template("create_new_poll.html", people="Enter one email address per line...")

@app.route('/vote_<poll_id>', methods=["POST","GET"])
def vote_poll_id(poll_id):
    user = request.args.get("user", None)
    # todo: handle None

    return vote_poll(poll_id, user)
    
# @app.route('/vote', methods=["POST","GET"])
# def vote_poll_param():
#     poll_id =  request.args.get('poll_id', None)
#     # todo: check None
#     return vote_poll(poll_id)

def vote_poll(poll_id, user):
    # todo: check valid
    # todo: check existing
    # todo check user

    # get question
    with open("data/poll_%s.json" % poll_id) as file:
        question = json.load(file)["question"]

    return render_template("vote_poll.html", question=question, poll_id=poll_id, user=user)

@app.route("/submit_vote", methods=["POST","GET"])
def submit_vote():
    if request.method == 'POST':
        options = request.form.get('options', None)
        name = request.form.get('name', None)
        poll_id = request.form.get('poll_id', None)
    else:
        options = request.args.get("options", None)
        name = request.args.get("name", None)
        poll_id = request.args.get("poll_id", None)
    print(options,name, poll_id)
    # todo: check invalid

    # check if user is eligible for voting
    with open("data/poll_%s.json" % poll_id, encoding="utf-8") as file:
        vote_data = json.load(file)

    hashed_name = hashlib.md5(name.encode("utf-8")).hexdigest()
    print(hashed_name)
    is_eligible = name in vote_data["people_hashes"]
    if not is_eligible:
        return "You are not allowed to vote here!"

    # check if user has already voted
    if hashed_name in vote_data["already_voted"]:
        return "you already voted for this poll!"
    
    # add vote
    print(options)
    num_votes = vote_data["people_hashes"].count(name)
    vote_data["num_%s" % options] += num_votes

    # mark user as already voted
    vote_data["already_voted"].append(hashed_name)

    # store vote
    with open("data/poll_%s.json" % poll_id, "w", encoding="utf-8") as file:
        json.dump(vote_data,file)

    # todo: show results
    url =  "%sresult_%s?user=%s" % (request.url_root, poll_id, hashed_name)
    return render_template("vote_submitted.html", result_url=url)

@app.route("/result_<poll_id>", methods=["GET,"POST"])
def result_url(poll_id):
    if request.method == 'POST':
        user = request.form.get('user', None)
    else:
        user = request.args.get("user", None)
    # get data
    with open("data/poll_%s.json" % poll_id, encoding="utf-8") as file:
        vote_data = json.load(file)

    # todo: only show results, when user has already voted
    if not user in vote_data["already_voted"]:
        return "you can only see results if you have already voted!"

    motion = vote_data["question"]
    num_yes = vote_data["num_yes"]
    num_no = vote_data["num_no"]
    num_abstain = vote_data["num_abstain"]
    num_votes = num_abstain + num_no + num_yes
    num_missing = len(vote_data["people_hashes"]) - num_votes
    people = vote_data["people_names"]
    people_num_votes = {}
    for p in people:
        people_num_votes[p] = people.count(p)
    print(people_num_votes)

    if num_missing < 0:
        print("something is fishy! more votes than registered voters!")

    # return render_template("result_view.html", motion=motion, num_votes=num_votes, num_yes=num_yes, num_no=num_no, num_abstain=num_abstain, num_missing=num_missing)
    return render_template("result_view_with_names.html", motion=motion, num_votes=num_votes, num_yes=num_yes, num_no=num_no, num_abstain=num_abstain, num_missing=num_missing, people=people_num_votes.items())

def send_all_emails(email_list, poll_url, question):
    # todo: handle duplicate emails as double votes
    already_sent = set()

    for email in email_list:
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
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

    email_hash = hashlib.md5((recipient).encode("utf-8")).hexdigest() # todo: this can be reconstructed, add salt 

    message = """From: Voting System <%s>\r\nTo: %s\r\nSubject: You have been invited to participate to a poll regarding %s\r\n

    click here to submit your vote: %s?user=%s
    you have %d vote(s).
    """ % (environ.get('SMTP_FROM'), recipient, question, poll_url, email_hash, num_votes)

    try:
        with smtplib.SMTP(environ.get('SMTP_HOST'), environ.get('SMTP_PORT')) as smtpObj:
            smtpObj.sendmail(sender, receivers, message)
            print("Successfully sent email")
    except smtplib.SMTPException:
        print("Error: unable to send email")

if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True)