from flask import Flask, Response, Request, request
from flask.json import jsonify
from pymongo import MongoClient
from db_init import db_init

app = Flask(__name__)
app.debug = True
db = MongoClient()['topspin']

Players = db['players']
Matches = db['matches']


def response_load(data=None, status="success", reason=None):
    resp = {}
    if data is not None:
        resp['data'] = data
    if status is not None:
        resp['status'] = status
    if reason is not None:
        resp['reason'] = reason
    return resp


def missing(field_list):
    return "Missing the following required fields: {}".format(', '.join(field_list))


@app.route("/")
def hello():
    return jsonify(**response_load(None))


@app.route("/api/v1/players", methods=['GET'])
def get_players():
    users = list(Players.find({}, {'_id': 0}))
    return jsonify(**response_load(data={'users': users}))

@app.route("/api/v1/players", methods=['POST'])
def add_player():
    json_request = request.get_json()
    required_fields = ['player_id', 'rating']
    optional_fields = ['first_name', 'k_factor', 'slack_id']

    _missing = []
    for rf in required_fields:
        if rf not in json_request:
            _missing.append(rf)

    if len(_missing) > 0:
        return jsonify(**response_load(reason=missing(_missing), status="error"))
    else:
        Players.insert_one({k: v for k, v in json_request.iteritems() if k in required_fields + optional_fields})

    return jsonify(**response_load(data="Inserted 1 player"))


@app.route("/api/v1/matches", methods=['GET'])
def get_matches():
    matches = list(Matches.find({}, {'_id': 0}))
    return jsonify(**response_load(data={'matches': matches}))


@app.route("/api/v1/players/<player_id>", methods=['GET'])
def get_player(player_id):
    user = Players.find_one({'player_id': player_id}, {'_id': 0})

    if user is None:
        res = {'users': []}
    else:
        res = {'users': [user]}
    return jsonify(**response_load(res))


@app.route("/api/v1/players/<player_id>/matches", methods=['GET'])
def get_player_matches(player_id):
    matches = list(Matches.find({'participants.player_id': {'$in': [player_id]}}, {'_id': 0}))
    return jsonify(**response_load(data={'matches': matches}))


if __name__ == '__main__':
    db_init(db)
    app.run()
