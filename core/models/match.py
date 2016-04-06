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
                       'participants']

    default_values = {
        'match_type': 'ping pong'
    }

    indexes = [
        {
            'fields': ['match_id'],
            'unique': True
        },
        {
            'fields': ['participants.player_id'],
            'check': False
        }
    ]

    def validate(self, *args, **kwargs):
        super(Match, self).validate(*args, **kwargs)
        for participant in self['participants']:
            assert participant['player_id'], "player_id is required: {}".format(participant)
