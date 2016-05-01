import uuid

import datetime
from flask import Flask, request, render_template, send_from_directory
from flask.json import jsonify
from mongokit import Connection
from mongokit.schema_document import SchemaDocumentError
from config import DB_HOST, DB_NAME, DB_PORT
from modules.exceptions import PlayerNotFoundException
from modules.elo import calculate_and_update
from models.metadata import Metadata
from models.rating import Rating
from models.match import Match
from models.player import Player
from models.player_stats import PlayerStats
from models.ranking import Ranking
from modules.probability import pairwise_probability_calculation as win_probability
from dateutil import parser
import json
import pytz


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


@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('../frontend/js', path)


@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory('../frontend/css', path)


@app.route("/")
def index():
    return render_template('leaderboard.html')


@app.route("/leaderboard")
def leaderboard():
    return render_template('leaderboard.html')


@app.route("/profile/<player_id>")
def render_profile(player_id):
    return render_template('profile.html', player_id=player_id)


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
    players = list(db.Player.find())
    return json_response(data={'players': [u.to_json_type() for u in players]})


@app.route("/api/v1/players", methods=['POST'])
def add_player():
    json_request = request.get_json()
    player = db.Player()

    for key, val in json_request.iteritems():
        if key not in player.viewkeys():
            continue
        if key == 'rating':
            val = float(val)
        player[key] = val
    try:
        player.validate()
        if db.Player.exists(player.player_id):
            return json_response(status="error", reason="Player already exists", code=400)
        player.save()
        return json_response()
    except SchemaDocumentError, e:
        return json_response(reason="Validation Error", data=str(e), status="error", code=400)


# Matches

@app.route("/api/v1/matches/<match_id>")
def get_match(match_id):
    match = db.Match.find_one({'match_id': match_id})

    if match is None:
        return json_response(data={}, code=400, status="error", reason="Match Not Found")
    else:
        res = match
        return json_response(res.to_json_type())


@app.route("/api/v1/matches")
def get_matches():
    matches = list(db.Match.find({}, {'_id': 0}))
    return json_response(data={'matches': [m.to_json_type() for m in matches]})


@app.route("/api/v1/matches", methods=['POST'])
def add_match():
    json_request = request.get_json()
    match = db.Match()

    for key, val in json_request.iteritems():
        if key not in match.viewkeys():
            continue
        # TODO: Make less hacky
        if key == "timestamp":
            match[key] = parser.parse(val, ignoretz=True)
        else:
            match[key] = val
    try:
        match.match_id = str(uuid.uuid4())
        match.validate()

        metadata = db.Metadata.find_one()
        if metadata is None:
            metadata = db.Metadata()
            metadata.matches.last_match_date = match.timestamp
            metadata.save()

        if metadata.matches.last_match_date > match.timestamp:
            force_recalculate_ratings()
        else:
            calculate_match_ratings(match)

        # We have to re-read metadata from db as it was modified during either force_recalculate_ratings or
        # calculate_match_ratings
        metadata = db.Metadata.find_one()
        metadata.matches.last_match_date = match.timestamp
        metadata.save()

        match.save()
        return json_response()

    except TypeError, e:
        return json_response(data=str(e), reason="Type Error", status="error", code=400)
    except SchemaDocumentError, e:
        return json_response(reason="Validation Error", data=str(e), status="error", code=400)


@app.route("/api/v1/matches/delete", methods=['POST'])
def delete_match():
    json_request = request.get_json()
    #TODO: AUTH
    if 'match_id' not in json_request:
        return json_response(data={}, reason="Missing match_id param", status="error", code=400)
    match = db.Match.find_one({'match_id': json_request['match_id']})
    if match:
        match.delete()
        if 'recalculate_ratings'in json_request and not json_request['recalculate_ratings']:
            word = "without"
        else:
            force_recalculate_ratings()
            word = "with"
        return json_response(data={}, reason="Successfully deleted match {} recalculation of ratings".format(word))
    else:
        return json_response(data={}, reason="Match does not exist", status="error", code=400)


# Player <-> Match

@app.route("/api/v1/players/<player_id>/matches")
def get_player_matches(player_id):
    limit = int(request.args.get('limit', '0'))
    sort = int(request.args.get('sort', '1'))
    _matches = list(db.Match.find({'participants.player_id': {'$in': [player_id]}}).sort('_id', sort).limit(limit))
    matches = []
    for m in _matches:
        opp = [p for p in m['participants'] if p['player_id'] != player_id][0]
        player = db.Player.find_one({'player_id': opp['player_id']})
        m['opponent_name'] = player.slack_name
        m['opponent'] = opp['player_id']
        m['result'] = 'W' if player_id == m['winner'] else 'L'
        m['scores'] = ':'.join([str(p['score']) for p in m['participants']])
        m['timestamp'] = m['timestamp'] + datetime.timedelta(hours=4) # TODO: fix hack for timezone issue
        del m['participants']
        matches.append(m)

    return json_response(data={'matches': [m.to_json_type() for m in matches]})


# Rating

@app.route("/api/v1/ratings")
def get_all_ratings():
    """
    Returns all historical ratings for all players
    """
    ratings = list(db.Rating.find())
    return json_response(data={'ratings': [r.to_json_type() for r in ratings]})


@app.route("/api/v1/ratings", methods=['PUT'])
def force_recalculate_ratings():
    """
    Clears the entire list of ratings and re-calculates everything from scratch
    """
    db[DB_NAME].drop_collection(Rating.__collection__)
    db[DB_NAME].drop_collection(PlayerStats.__collection__)
    db.Player.reset_all_ratings()

    counter = 0
    last_match = None
    for match in db.Match.find().sort('_id', 1):
        try:
            calculate_match_ratings(match)
            counter += 1
            last_match = match

        except PlayerNotFoundException:
            return json_response(status="error", reason="One of the matches has an invalid player", code=500)

    # Update last match date in metadata to last match processed
    metadata = db.Metadata.find_one()
    metadata.matches.last_match_date = last_match.timestamp
    metadata.save()

    return json_response(data="{} matches processed".format(counter))


# Player <-> Rating

@app.route("/api/v1/players/<player_id>/ratings")
def get_player_ratings(player_id):
    _sort_order = request.args.get('sort', 'ascending')
    sort_order = 1 if _sort_order == 'ascending' else -1
    ratings = list(db.Rating.find({'player_id': player_id}).sort('timestamp', sort_order))
    return json_response(data={'ratings': [r.to_json_type() for r in ratings]})


# Player <-> Stats
@app.route("/api/v1/players/<player_id>/stats")
def get_player_stats(player_id):
    user = db.PlayerStats.find_one({'player_id': player_id})

    if user is None:
        return json_response(data={}, code=400, status="error", reason="User Not Found")
    else:
        res = user
        return json_response(res.to_json_type())

# Rankings

@app.route("/api/v1/rankings")
def get_rankings():
    limit = int(request.args.get('top', '10'))
    player_ratings = {}
    for rating in db.Rating.find().sort('_id', -1):
        if rating.player_id not in player_ratings:
            rating_obj = {
                'player_id': rating.player_id,
                'rating': rating.rating
            }
            player_ratings[rating.player_id] = rating_obj

    sorted_data = sorted([player_ratings[player] for player in player_ratings],
                         key=lambda doc: doc['rating'],
                         reverse=True)

    with_ranking = []
    for index, rank in enumerate(sorted_data):
        player_info = db.Player.find_one({'player_id': rank['player_id']})
        if player_info:
            for key in ['slack_name', 'real_name', 'profile_picture', 'num_games_played', 'num_games_won']:
                rank[key] = player_info[key]
        rank['rank'] = index + 1
        with_ranking.append(rank)

    if limit == -1:
        return json_response(data={'rankings': with_ranking})
    return json_response(data={'rankings': with_ranking[:limit]})


# Misc

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


def calculate_match_ratings(match):
    winner_id = match.winner
    winner = loser = None
    for participant in match.participants:
        player = db.Player.find_one({'player_id': participant['player_id']})
        if player is None:
            raise PlayerNotFoundException
        if player.player_id == winner_id:
            winner = player
            winner.num_games_won += 1
        else:
            loser = player

    calculate_and_update(winner, loser)
    add_to_stats(match, winner, loser)
    for player in [winner, loser]:
        db.Rating({
            'player_id': player.player_id,
            'rating': player.rating,
            'k_factor': player.k_factor,
            'match_id': match.match_id,
            'timestamp': match.timestamp
        }).save()
        player.last_game_played = match.timestamp
        player.num_games_played += 1
        if player.num_games_played >= 40:
            player.k_factor = 8

        player.save()

    metadata = db.Metadata.find_one()
    if metadata is None:
        metadata = db.Metadata()
    metadata.ratings.last_date_processed = match.timestamp
    metadata.ratings.last_updated = datetime.datetime.now()
    metadata.save()


def add_to_stats(match, winner, loser):
    ws = db.PlayerStats.find_one({'player_id': winner.player_id})
    ls = db.PlayerStats.find_one({'player_id': loser.player_id})

    if ws is None:
        ws = db.PlayerStats()
        ws.player_id = winner.player_id
    if ls is None:
        ls = db.PlayerStats()
        ls.player_id = loser.player_id

    if match.participants[0]['player_id'] == winner.player_id:
        w_score = match.participants[0]['score']
        l_score = match.participants[1]['score']
    else:
        w_score = match.participants[1]['score']
        l_score = match.participants[0]['score']

    pr = win_probability(winner, loser)
    found = False
    for mu in ws.match_ups:
        if mu['opp_id'] == loser.player_id:
            found = True
            prev_ppg = mu['games_played_against'] * mu['ppg_against']
            mu['last_played_against'] = match.timestamp
            mu['games_played_against'] += 1
            mu['games_won_against'] += 1
            mu['ppg_against'] = (prev_ppg + w_score) / float(mu['games_played_against'])
            mu['pr_win_against'] = pr[winner.player_id]['win']
            break
    if not found:
        ws.match_ups.append({
            'opp_id': loser.player_id,
            'opp_slack_name': loser.slack_name,
            'opp_profile_picture': loser.profile_picture,
            'last_played_against': match.timestamp,
            'games_played_against': 1,
            'games_won_against': 1,
            'games_lost_against': 0,
            'ppg_against': float(w_score),
            'pr_win_against': pr[winner.player_id]['win']
        })

    found = False
    for mu in ls.match_ups:
        if mu['opp_id'] == winner.player_id:
            found = True
            prev_ppg = mu['games_played_against'] * mu['ppg_against']
            mu['last_played_against'] = match.timestamp
            mu['games_played_against'] += 1
            mu['games_lost_against'] += 1
            mu['ppg_against'] = (prev_ppg + l_score) / float(mu['games_played_against'])
            mu['pr_win_against'] = pr[loser.player_id]['win']
            break
    if not found:
        ls.match_ups.append({
            'opp_id': winner.player_id,
            'opp_slack_name': winner.slack_name,
            'opp_profile_picture': winner.profile_picture,
            'last_played_against': match.timestamp,
            'games_played_against': 1,
            'games_won_against': 0,
            'games_lost_against': 1,
            'ppg_against': float(l_score),
            'pr_win_against': pr[loser.player_id]['win']
        })

    # Prev Data
    ## PPG
    winner_prev_point_sum = ws.num_games_played.total * ws.ppg
    winner_ppsum_win = ws.num_games_played.won * ws.win_ppg
    loser_prev_point_sum = ls.num_games_played.total * ls.ppg
    loser_ppsum_lose = ls.num_games_played.lost * ls.lose_ppg

    ## PD
    winner_prev_diff_sum = ws.num_games_played.total * ws.ppg_diff
    winner_pdsum_win = ws.num_games_played.won * ws.win_ppg_diff
    loser_prev_diff_sum = ls.num_games_played.total * ls.ppg_diff
    loser_pdsum_lose = ls.num_games_played.lost * ls.lose_ppg_diff

    # GP
    ws.num_games_played.total += 1
    ls.num_games_played.total += 1
    ws.num_games_played.won += 1
    ls.num_games_played.lost += 1

    # Personal PPG
    ws.ppg = (winner_prev_point_sum + w_score) / float(ws.num_games_played.total)
    ws.win_ppg = (winner_ppsum_win + w_score) / float(ws.num_games_played.won)
    ls.ppg = (loser_prev_point_sum + l_score) / float(ls.num_games_played.total)
    ls.lose_ppg = (loser_ppsum_lose + l_score) / float(ls.num_games_played.lost)

    # PPG Diff
    diff = w_score - l_score
    ws.ppg_diff = (winner_prev_diff_sum + diff) / float(ws.num_games_played.total)
    ws.win_ppg_diff = (winner_pdsum_win + diff) / float(ws.num_games_played.won)
    ls.ppg_diff = (loser_prev_diff_sum - diff) / float(ls.num_games_played.total)
    ls.lose_ppg_diff = (loser_pdsum_lose - diff) / float(ls.num_games_played.lost)

    # Current Streaks
    if ws.current_streak.type == 'win':
        ws.current_streak.streak += 1
    else:
        ws.current_streak.streak = 1
        ws.current_streak.type = 'win'

    if ls.current_streak.type == 'lose':
        ls.current_streak.streak += 1
    else:
        ls.current_streak.streak = 1
        ls.current_streak.type = 'lose'

    # Streak Records
    if ws.current_streak.streak > ws.longest_win_streak:
        ws.longest_win_streak = ws.current_streak.streak
    if ls.current_streak.streak > ls.longest_lose_streak:
        ls.longest_lose_streak = ls.current_streak.streak

    ws.save()
    ls.save()


def ensure_indexes():
    # unfortunately, mongokit does NOT do indexes automatically -- false advertising
    db.Player.generate_index(db[DB_NAME][Player.__collection__])
    db.Match.generate_index(db[DB_NAME][Match.__collection__])
    db.Rating.generate_index(db[DB_NAME][Rating.__collection__])
    db.Ranking.generate_index(db[DB_NAME][Ranking.__collection__])
    db.PlayerStats.generate_index(db[DB_NAME][PlayerStats.__collection__])


if __name__ == '__main__':
    db = Connection(host=DB_HOST, port=DB_PORT)
    db.register([Player, Match, Rating, Metadata, Ranking, PlayerStats])
    ensure_indexes()
    app.run(host='0.0.0.0')
