from pymongo import MongoClient
from config import DB_HOST, DB_NAME, DB_PORT
import argparse
import random
import datetime


def insert_players(num_players=20):
    print "Inserting {} players".format(num_players)

    names = set()
    to_insert = []
    first_names = ['alexander', 'alexis', 'bob', 'cory', 'dave', 'emma', 'george', 'greg',
                   'iggy', 'jamie', 'gerald', 'laurie', 'max', 'john', 'olesha', 'johannes',
                   'sachs', 'rory', 'samuel', 'stephen', 'tony', 'maggie', 'woj', 'geoff', 'yessar']
    last_names = ['atkins', 'lee', 'greco', 'paul', 'lao', 'barracuda', 'zee', 'escobar',
                  'gonzaga', 'lowe', 'tsang', 'sword', 'sears', 'carp', 'rivers', 'hsieh',
                  'happy', 'schnauzer', 'bourne']
    for i in range(num_players):
        names.add("{}{}".format(first_names[random.randint(0, len(first_names) - 1)],
                                last_names[random.randint(0, len(last_names) - 1)]))

    for name in list(names):
        to_insert.append({
            'player_id': name,
            'rating': float(random.randint(900, 1500)),
            'k_factor': random.randint(8, 15)
        })

    db['players'].ensure_index('player_id', 1)
    db['players'].insert_many(to_insert)
    return list(names)


def insert_matches(player_names, num_matches):
    print "Inserting matches for {} people".format(len(player_names))
    to_insert = []
    start_date = datetime.datetime.today()
    for i in range(num_matches):
        winner = player_names[random.randint(0, len(player_names) - 1)]
        loser = player_names[random.randint(0, len(player_names) - 1)]
        if winner == loser:
            continue

        winner_score = 21
        loser_score = random.randint(0, 19)
        to_insert.append({
            'match_id': i,
            'participants': sorted([{
                'player_id': winner,
                'score': winner_score
            }, {
                'player_id': loser,
                'score': loser_score
            }], key=lambda d: d['player_id']),
            'timestamp': start_date + datetime.timedelta(days=random.randint(i - 1, i)),
            'winner': winner
        })

    db['matches'].drop()
    db['matches'].ensure_index('participants.player_id', 1)
    db['matches'].ensure_index('match_id', 1)
    db['matches'].insert_many(to_insert)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Loads some fake data for ladder')
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--num-players', type=int, default=20)
    parser.add_argument('--num-matches', type=int, default=20)
    args = parser.parse_args()

    # load config
    db = MongoClient(DB_HOST, DB_PORT)[DB_NAME]

    if args.force:
        print "Force dropping collections"
        db['players'].drop()
        db['matches'].drop()

    names_inserted = insert_players(args.num_players)
    insert_matches(names_inserted, args.num_matches)
