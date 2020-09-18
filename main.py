import json
import random
from flask import Flask, request, render_template, redirect, url_for
import hashlib

app = Flask(__name__)


@app.route('/')
def root():
    return redirect(url_for('create_poll'))

@app.route('/test')
def test():
	return "test success at " + request.url_root

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
    question = request.args.get("question",None)
    option = request.args.get("option",None)
    people = request.args.get("people",None)
    # todo: handle invalid/None
    # todo: handle empty
    print(question)
    people_list = people.replace("\r","").split("\n")
    print(people_list)

    poll_id = store_poll(question, people_list)
    url = "%svote_%s" % (request.url_root, poll_id)
    return render_template("poll_created.html", poll_id=poll_id, url=url)

@app.route('/create', methods=["POST","GET"])
def create_poll():
    # todo: show creation site
    return render_template("create_new_poll.html")

@app.route('/vote_<poll_id>', methods=["POST","GET"])
def vote_poll_id(poll_id):
    return vote_poll(poll_id)
    
@app.route('/vote', methods=["POST","GET"])
def vote_poll_param():
    poll_id =  request.args.get('poll_id', None)
    # todo: check None
    return vote_poll(poll_id)

def vote_poll(poll_id):
    # todo: check valid
    # todo: check existing

    # get question
    with open("data/poll_%s.json" % poll_id) as file:
        question = json.load(file)["question"]

    return render_template("vote_poll.html", question=question, poll_id=poll_id)

@app.route("/submit_vote")
def submit_vote():
    options = request.args.get("options",None)
    name = request.args.get("name",None)
    poll_id = request.args.get("poll_id",None)
    # todo: check invalid

    # check if user is eligible for voting
    with open("data/poll_%s.json" % poll_id, encoding="utf-8") as file:
        vote_data = json.load(file)

    hashed_name = hashlib.md5(name.encode("utf-8")).hexdigest()
    print(hashed_name)
    is_eligible = hashed_name in vote_data["people_hashes"]
    if not is_eligible:
        return "You are not allowed to vote here!"

    # check if user has already voted
    if hashed_name in vote_data["already_voted"]:
        return "you already voted for this poll!"
    
    # add vote
    print(options)
    vote_data["num_%s" % options] += 1

    # mark user as already voted
    vote_data["already_voted"].append(hashed_name)

    # store vote
    with open("data/poll_%s.json" % poll_id, "w", encoding="utf-8") as file:
        json.dump(vote_data,file)

    # todo: show results
    return "successfully voted!"


@app.route("/result_<poll_id>")
def result_url(poll_id):
    # get data
    with open("data/poll_%s.json" % poll_id, encoding="utf-8") as file:
        vote_data = json.load(file)

    motion = vote_data["question"]
    num_yes = vote_data["num_yes"]
    num_no = vote_data["num_no"]
    num_abstain = vote_data["num_abstain"]
    num_votes = num_abstain + num_no + num_yes
    num_missing = len(vote_data["people_hashes"]) - num_votes
    people = vote_data["people_names"]

    if num_missing < 0:
        print("something is fishy! more votes than registered voters!")

    # return render_template("result_view.html", motion=motion, num_votes=num_votes, num_yes=num_yes, num_no=num_no, num_abstain=num_abstain, num_missing=num_missing)
    return render_template("result_view_with_names.html", motion=motion, num_votes=num_votes, num_yes=num_yes, num_no=num_no, num_abstain=num_abstain, num_missing=num_missing, people=people)

if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True)