import datetime
from mongokit import Document
from config import DB_NAME


class Rating(Document):
    __database__ = DB_NAME
    __collection__ = 'ratings'
    use_dot_notation = True

    structure = {
        'player_id': basestring,
        # match data used to calculate this rating
        'match_id': basestring,
        'timestamp': datetime.datetime,
        # rating after match
        'rating': float,
        # k_factor used to calculate this rating
        'k_factor': int
    }

    required_fields = ['player_id', 'match_id', 'rating', 'k_factor']

    indexes = [
        {
            'fields': ['player_id', 'match_id'],
            'unique': True
        },
        {
            'fields': ['player_id']
        },
        {
            'fields': ['player_id', 'rating']
        }
    ]