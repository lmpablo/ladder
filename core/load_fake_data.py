from mongokit import Connection
from models.match import Match
from models.player import Player
from config import DB_HOST, DB_NAME, DB_PORT
import argparse
import random
import datetime


def insert_players(num_players=20):
    connection.Player.generate_index(connection[DB_NAME][Player.__collection__])

    if connection.Player.find_one():
        return [p['player_id'] for p in connection.Player.find().limit(num_players)]

    print "Inserting {} players".format(num_players)

    first_names = ['alexander', 'alexis', 'bob', 'cory', 'dave', 'emma', 'george', 'greg',
                   'iggy', 'jamie', 'gerald', 'laurie', 'max', 'john', 'olesha', 'johannes', 'shawn',
                   'sachs', 'rory', 'samuel', 'stephen', 'tony', 'maggie', 'woj', 'geoff', 'yessar',
                   'peter', 'richard']
    last_names = ['atkins', 'lee', 'greco', 'paul', 'lao', 'barracuda', 'zee', 'escobar',
                  'gonzaga', 'lowe', 'tsang', 'sears', 'carp', 'rivers', 'hsieh',
                  'happy', 'schnauzer', 'bourne', 'minnows', 'gregory', 'hendricks']
    random.shuffle(first_names)
    random.shuffle(last_names)
    names = zip(first_names, last_names)

    for fname, lname in list(names)[:num_players]:
        name = "{}{}".format(fname, lname)
        player = connection.Player()
        player.player_id = name
        player.first_name = fname.capitalize()
        # TODO: don't randomize rating, actually calculate it
        player.rating = float(random.randint(900, 1500))
        player.k_factor = random.randint(8, 15)
        player.save()

    return ['{}{}'.format(fname, lname) for fname, lname in names[:num_players]]


def insert_matches(player_names, num_matches):
    connection.Match.generate_index(connection[DB_NAME][Match.__collection__])

    if connection.Match.find_one():
        return
    print "Inserting matches for {} people".format(len(player_names))

    start_date = datetime.datetime.today()
    for i in range(num_matches):
        winner = player_names[random.randint(0, len(player_names) - 1)]
        loser = player_names[random.randint(0, len(player_names) - 1)]
        if winner == loser:
            continue

        timestamp = start_date + datetime.timedelta(days=random.randint(i - 1, i))

        # update player stats
        winner_p = connection.Player.find_one({'player_id': winner})
        loser_p = connection.Player.find_one({'player_id': loser})

        winner_p.num_games_played += 1
        loser_p.num_games_played += 1

        if winner_p.last_game_played is None or winner_p.last_game_played < timestamp:
            winner_p.last_game_played = timestamp

        if loser_p.last_game_played is None or loser_p.last_game_played < timestamp:
            loser_p.last_game_played = timestamp

        winner_p.save()
        loser_p.save()

        winner_score = 21
        loser_score = random.randint(0, 19)
        match = connection.Match()
        match.match_id = str(i)
        match.participants = sorted([{
                'player_id': winner,
                'score': winner_score
            }, {
                'player_id': loser,
                'score': loser_score
            }], key=lambda d: d['player_id'])
        match.timestamp = timestamp
        match.winner = winner
        match.save()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Loads some fake data for ladder')
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--num-players', type=int, default=20)
    parser.add_argument('--num-matches', type=int, default=20)
    args = parser.parse_args()

    # load config
    connection = Connection(host=DB_HOST, port=DB_PORT)
    connection.register([Player, Match])

    if args.force:
        print "Force dropping collections"
        connection[DB_NAME].drop_collection(Player.__collection__)
        connection[DB_NAME].drop_collection(Match.__collection__)

    names_inserted = insert_players(args.num_players)
    insert_matches(names_inserted, args.num_matches)
