from flask import Flask, request, render_template
from flask.json import jsonify
from mongokit import Connection
from mongokit.schema_document import SchemaDocumentError
from config import DB_HOST, DB_NAME, DB_PORT
from models.match import Match
from models.player import Player
from modules.probability import pairwise_probability_calculation as win_probability
import json

import datetime
from dateutil import parser

app = Flask(__name__, template_folder='../frontend/')
app.config.from_pyfile('config.py')


def json_response(data=None, status="success", reason=None, code=200):
    response_object = {}

    if data is not None:
        response_object['data'] = data
    if status is not None:
        response_object['status'] = status
    if reason is not None:
        response_object['reason'] = reason

    return jsonify(**response_object), code


def missing(field_list):
    return "Missing the following required fields: {}".format(', '.join(field_list))


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/matches")
def matches_view():
    # TODO: Access the API instead of the function
    matches = json.loads(get_matches()[0].get_data())
    return render_template('matches/list.html', matches=matches)

# Players

@app.route("/api/v1/players/<player_id>")
def get_player(player_id):
    user = db.Player.find_one({'player_id': player_id})

    if user is None:
        return json_response(data={}, code=400, status="error", reason="User Not Found")
    else:
        res = user
        return json_response(res.to_json_type())

@app.route("/api/v1/players")
def get_players():
    users = list(db.Player.find())
    return json_response(data={'users': [u.to_json_type() for u in users]})

@app.route("/api/v1/players", methods=['POST'])
def add_player():
    json_request = request.get_json()
    player = db.Player()

    for key, val in json_request.iteritems():
        if key not in player.viewkeys():
            continue
        player[key] = val
    try:
        player.validate()
        if db.Player.find_one({'player_id': json_request['player_id']}) is not None:
            return json_response(status="error", reason="Player already exists", code=400)
        player.save()
        return json_response()
    except SchemaDocumentError, e:
        return json_response(reason="Validation Error", data=str(e), status="error", code=400)

# Matches

@app.route("/api/v1/matches/<match_id>")
def get_match(match_id):
    match = db.Match.find_one({'match_id': match_id})
    print type(match)

    if match is None:
        return json_response(data={}, code=400, status="error", reason="Match Not Found")
    else:
        res = match
        return json_response(res.to_json_type())

@app.route("/api/v1/matches")
def get_matches():
    matches = list(db.Match.find({}, {'_id': 0}))
    return json_response(data={'matches': matches})

@app.route("/api/v1/matches", methods=['POST'])
def add_match():
    json_request = request.get_json()
    match = db.Match()

    for key, val in json_request.iteritems():
        if key not in match.viewkeys():
            continue
        if key == "timestamp":
            match[key] = parser.parse(val)
        else:
            match[key] = val
    try:
        match.validate()
        if db.Match.find_one({'match_id': json_request['match_id']}) is not None:
            return json_response(status="error", reason="Match already exists", code=400)
        match.save()
        return json_response()
    except SchemaDocumentError, e:
        return json_response(reason="Validation Error", data=str(e), status="error", code=400)


# Player <-> Match
@app.route("/api/v1/players/<player_id>/matches", methods=['GET'])
def get_player_matches(player_id):
    matches = list(db.Match.find({'participants.player_id': {'$in': [player_id]}}))
    return json_response(data={'matches': [m.to_json_type() for m in matches]})


@app.route("/api/v1/probability", methods=['POST'])
def get_probability():
    json_request = request.get_json()

    p1 = json_request.get('player_id_1')
    p2 = json_request.get('player_id_2')

    if p1 is None or p2 is None:
        return json_response(status="error", reason="Need both player_id_1 and player_id_2", code=400)

    player1 = db.Player.find_one({'player_id': p1})
    player2 = db.Player.find_one({'player_id': p2})

    if player1 is None or player2 is None:
        return json_response(status="error", reason="Need valid player_id_1 and player_id_2", code=400)

    return json_response(data=win_probability(player1, player2))


def ensure_indexes():
    # unfortunately, mongokit does NOT do indexes automatically -- false advertising
    db.Player.generate_index(db[DB_NAME][Player.__collection__])
    db.Match.generate_index(db[DB_NAME][Match.__collection__])


if __name__ == '__main__':
    db = Connection(host=DB_HOST, port=DB_PORT)
    db.register([Player, Match])
    ensure_indexes()
    app.run()
