from mongokit import Document
from config import DB_NAME
import datetime


class Metadata(Document):
    __database__ = DB_NAME
    __collection__ = 'metadata'
    use_dot_notation = True

    structure = {
        'ratings': {
            'last_date_processed': datetime.datetime
        },
        'matches': {
            'last_match_date': datetime.datetime
        }
    }

    required_fields = []
    default_values = {
        'ratings.last_date_processed': datetime.datetime(1970, 1, 1)
    }
