import math
from collections import defaultdict


class Elo(object):
    def __init__(self):
        self.calculator = EloCalculator()

    def match(self, winner, loser, draw=False, pd=None):
        print "{} {} {}".format(winner.name, "draw with" if draw else "beat", loser.name)
        s1 = 0.5 if draw else 1.0
        s2 = 0.5 if draw else 0
        pd = None if draw else pd
        u1, u2 = self.calculator.calculate_update(winner, loser, s1, s2, pd)

        winner.update_rating(u1)
        loser.update_rating(u2)

class EloCalculator(object):
    def __init__(self):
        pass

    def calculate_update(self, winner, loser, s1, s2, pd):
        expected_winner = self.calculate_expected(winner, loser)
        expected_loser = 1 - expected_winner

        if pd is None:
            mvm = 1.0
        else:
            mvm = math.log1p(abs(pd)) * (2.2 / ((winner.get_rating() - loser.get_rating()) * 0.001 + 2.2))

        update_winner = (mvm * winner.k) * (s1 - expected_winner)
        update_loser = (mvm * loser.k) * (s2 - expected_loser)

        return update_winner, update_loser

    def calculate_expected(self, a, b):
        q_a = a.rating / float(400)
        q_b = b.rating / float(400)
        return q_a / (q_a + q_b)

class Player(object):
    def __init__(self, name, rating=-1, k=40):
        self.name = name
        self.rating = float(rating)
        self.k = k

    def update_rating(self, diff):
        self.rating += diff

    def get_rating(self):
        return self.rating

    def __str__(self):
        return "{} ({})".format(self.name, "{:0.05}".format(self.rating) if self.rating > 0 else "UNRANKED")

players = {}
for p in [('LP', 1000, 12), ('JB', 1000, 12), ('SL', 950, 12),
          ('CB', 1000, 12), ('JE', 1000, 12), ('EB', 950, 12),
          ('LC', 950, 12), ('YG', 1000, 12), ('TL', -1, 12),
          ('WG', -1, 12), ('JS', -1, 12), ('AA', -1, 12),
          ('AV', 950, 12), ('OK', -1, 12), ('BL', 950, 12)]:
    players[p[0]] = Player(p[0], p[1], p[2])

elo = Elo()
matches = [('LC', 'EB'),
           ('EB', 'LC'),
           ('LC', 'EB'),
           ('LP', 'JB'),
           ('JB', 'LP'),
           ('LP', 'JB'),
           ('YG', 'JE'),
           ('JE', 'YG'),
           ('JE', 'YG'),
           ('JE', 'LP'),
           ('LP', 'JE'),
           ('JE', 'LP'),
           ('CB', 'SL'),
           ('CB', 'LP'),
           ('CB', 'JB'),
           ('JB', 'LP'),
           ('LP', 'JB'),
           ('JB', 'YG'),
           ('JB', 'YG'),
           ('JB', 'LP')]

match_pairs = defaultdict(lambda: defaultdict(int))

scores = defaultdict(list)

for idx, match in enumerate(matches):
    elo.match(players[match[0]], players[match[1]])
    obj_a = {
        'rating': players[match[0]].rating,
        'match-id': idx
    }
    obj_b = {
        'rating': players[match[1]].rating,
        'match-id': idx
    }

    scores[players[match[0]].name].append(obj_a)
    scores[players[match[1]].name].append(obj_b)
    match_pairs[match[0]][match[1]] += 1
    match_pairs[match[1]][match[0]] += 1


for idx, player in enumerate(sorted(players, key=lambda x: players[x].rating, reverse=True)):
    print "#{} ".format(idx + 1) + str(players[player])


for player, score_list in scores.iteritems():
    for s in score_list:
        print "{} after match #{}: {}".format(player, s['match-id'], s['rating'])

for pair in match_pairs:
    print pair, dict(match_pairs[pair])
