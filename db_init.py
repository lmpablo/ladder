import random
import datetime


def insert_players(db):
    names = set()
    to_insert = []
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    for i in range(20):
        names.add("{}{}{}".format(alphabet[random.randint(0, 25)],
                                alphabet[random.randint(0, 25)],
                                alphabet[random.randint(0, 25)]))

    for name in list(names):
        to_insert.append({
            'player_id': name,
            'rating': float(random.randint(900, 1500)),
            'k_factor': random.randint(8, 15)
        })

    db['players'].drop()
    db['players'].ensure_index('player_id', 1)
    db['players'].insert_many(to_insert)
    return list(names)


def insert_matches(db, player_names):
    to_insert = []
    start_date = datetime.datetime(2016, 03, 02)
    for i in range(20):
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
            'timestamp': start_date + datetime.timedelta(days=i),
            'winner': winner
        })

    db['matches'].drop()
    db['matches'].ensure_index('participants.player_id', 1)
    db['matches'].ensure_index('match_id', 1)
    db['matches'].insert_many(to_insert)


def run_setup(db):
    player_names = insert_players(db)
    insert_matches(db, player_names)


def db_init(db):
    is_setup = db['metadata'].find_one({'setup': True})
    if is_setup is None:
        run_setup(db)
        db['metadata'].insert({'setup': True})
