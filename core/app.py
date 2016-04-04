from flask import Flask, Response, Request, request, Blueprint
from flask.json import jsonify
from pymongo import MongoClient
from cerberus import Validator
from models.player import PlayerSchema
from models.match import MatchSchema
from modules.probability import pairwise_probability_calculation

app = Flask(__name__)
app.config.from_pyfile('config.py')

db = MongoClient(app.config.get('DB_HOST', 'localhost'),
                 app.config.get('DB_PORT', 27017))[app.config.get('DATABASE', 'ladder')]

Players = db['players']
Matches = db['matches']

players_validator = Validator(PlayerSchema)
matches_validator = Validator(MatchSchema)


class Player(object):
    def __init__(self, d):
        for key, val in d.iteritems():
            setattr(self, key, val)


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


@app.route("/api/v1/players")
def get_players():
    users = list(Players.find({}, {'_id': 0}))
    return jsonify(**response_load(data={'users': users}))


@app.route("/api/v1/players", methods=['POST'])
def add_player():
    json_request = request.get_json()
    is_valid = players_validator.validate(json_request)
    if is_valid:
        if Players.find_one({'player_id': json_request['player_id']}) is not None:
            return jsonify(**response_load(status="error", reason="Player already exists")), 500
        Players.insert_one(json_request)
        return jsonify(**response_load())
    else:
        return jsonify(**response_load(reason="Validation errors", data=players_validator.errors, status="error")), 400


@app.route("/api/v1/matches")
def get_matches():
    matches = list(Matches.find({}, {'_id': 0}))
    return jsonify(**response_load(data={'matches': matches}))


@app.route("/api/v1/players/<player_id>")
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


@app.route("/api/v1/probability", methods=['POST'])
def get_probability():
    json_request = request.get_json()

    p1 = json_request.get('player_id_1')
    p2 = json_request.get('player_id_2')

    if p1 is None or p2 is None:
        return jsonify(**response_load(status="error", reason="Need both player_id_1 and player_id_2")), 400

    player1 = Player(Players.find_one({'player_id': p1}))
    player2 = Player(Players.find_one({'player_id': p2}))

    if player1 is None or player2 is None:
        return jsonify(**response_load(status="error", reason="Need both player_id_1 and player_id_2")), 400

    return jsonify(**response_load(data=pairwise_probability_calculation(player1, player2)))


if __name__ == '__main__':
    app.run()
