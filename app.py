from flask import Flask, Response
from flask.json import jsonify
from pymongo import MongoClient
from db_init import db_init

app = Flask(__name__)
app.debug = True
db = MongoClient()['topspin']

Players = db['players']
Matches = db['matches']


def response_load(data, status="success"):
    return dict(status=status, data=data)


@app.route("/")
def hello():
    return "TOPSPIN"


@app.route("/players", methods=['GET'])
def get_players():
    users = list(Players.find({}, {'_id': 0}))
    return jsonify(**response_load(data={'users': users}))


@app.route("/matches", methods=['GET'])
def get_matches():
    matches = list(Matches.find({}, {'_id': 0}))
    return jsonify(**response_load(data={'matches': matches}))


@app.route("/players/<player_id>", methods=['GET'])
def get_player(player_id):
    user = Players.find_one({'player_id': player_id}, {'_id': 0})

    if user is None:
        res = {'users': []}
    else:
        res = {'users': [user]}
    return jsonify(**response_load(res))


@app.route("/players/<player_id>/matches", methods=['GET'])
def get_player_matches(player_id):
    matches = list(Matches.find({'participants.player_id': {'$in': [player_id]}}, {'_id': 0}))
    return jsonify(**response_load(data={'matches': matches}))


if __name__ == '__main__':
    db_init(db)
    app.run()
