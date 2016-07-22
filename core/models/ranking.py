from mongokit import Document
from config import DB_NAME
import datetime


class Ranking(Document):
    __database__ = DB_NAME
    __collection__ = 'ranking'
    use_dot_notation = True

    structure = {
        'timestamp': datetime.datetime,
        'rankings': [{
            'player_id': basestring,
            'real_name': basestring,
            'slack_name': basestring,
            'profile_picture': basestring,
            'rating': float,
            'num_games_played': int,
            'num_games_won': int,
            'rank': int,

        }]
    }

    required_fields = ['timestamp', 'rankings']

    default_values = {
        'timestamp': datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
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
            assert player['num_games_played'], "num_games for rankings is required: {}".format(player)
        super(Ranking, self).validate(*args, **kwargs)


