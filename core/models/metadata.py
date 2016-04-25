from mongokit import Document
from config import DB_NAME
import datetime
import pytz


class Metadata(Document):
    __database__ = DB_NAME
    __collection__ = 'metadata'
    use_dot_notation = True

    structure = {
        'ratings': {
            'last_date_processed': datetime.datetime,
            'last_updated': datetime.datetime
        },
        'matches': {
            'last_match_date': datetime.datetime
        },
        'rankings': {
            'last_updated': datetime.datetime
        }
    }

    required_fields = []
    default_values = {
        'ratings.last_date_processed': datetime.datetime(1970, 1, 1),
        'matches.last_match_date': datetime.datetime(1970, 1, 1),
        'ratings.last_updated': datetime.datetime(1970, 1, 1),
        'rankings.last_updated': datetime.datetime(1970, 1, 1)
    }
