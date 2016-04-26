from mongokit import Document
from config import DB_NAME
import datetime


class Ranking(Document):
    __database__ = DB_NAME
    __collection__ = 'matches'
    use_dot_notation = True

    structure = {
        'timestamp': datetime.datetime,
        'last_updated': datetime.datetime,
        'rankings': [{
            'player_id': basestring,
            'rating': int,
            'rank': int
        }]
    }

    required_fields = ['timestamp', 'rankings']

    default_values = {
        'timestamp': datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0),
        'last_updated': datetime.datetime.now()
    }

    indexes = [
        {
            'fields': ['timestamp'],
            'unique': True
        }
    ]

    def validate(self, *args, **kwargs):
        for player in self['rankings']:
            assert player['player_id'], "player_id for rankings is required: {}".format(player)
            assert player['rating'], "rating for rankings is required: {}".format(player)
            assert player['rank'], "rank for rankings is required: {}".format(player)
        super(Ranking, self).validate(*args, **kwargs)


