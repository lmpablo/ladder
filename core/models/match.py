from mongokit import Document
from config import DB_NAME
import datetime


class Match(Document):
    __database__ = DB_NAME
    __collection__ = 'matches'
    use_dot_notation = True

    structure = {
        'match_id': basestring,
        'timestamp': datetime.datetime,
        'winner': basestring,
        'match_type': basestring,
        'participants': [{
            'player_id': basestring,
            'score': int
        }]
    }

    required_fields = ['match_id',
                       'timestamp',
                       'winner'
                       ]

    default_values = {
        'match_type': 'ping pong',
        'timestamp': datetime.datetime.now()
    }

    indexes = [
        {
            'fields': ['match_id'],
            'unique': True
        },
        {
            'fields': ['participants.player_id'],
            'check': False
        },
        {
            'fields': ['timestamp']
        }
    ]

    def validate(self, *args, **kwargs):
        for participant in self['participants']:
            assert participant['player_id'], "player_id for participans is required: {}".format(participant)
            if 'score' not in participant:
                participant['score'] = -1
        super(Match, self).validate(*args, **kwargs)

    def get_winner(self):
        return self.connection.Player.find_one({'player_id': self['winner']})

