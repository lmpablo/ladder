from mongokit import Document
from config import DB_NAME
import datetime


class Player(Document):
    __database__ = DB_NAME
    __collection__ = 'players'
    use_dot_notation = True

    structure = {
        'player_id': basestring,
        'first_name': basestring,
        'rating': float,
        'k_factor': int,
        'last_game_played': datetime.datetime,
        'num_games_played': int
    }

    required_fields = ['player_id']
    default_values = {
        'num_games_played': 0
    }

    indexes = [
        {
            'fields': ['player_id'],
            'unique': True
        }
    ]

    def reset_all_ratings(self):
        for player in self.connection.Player.find():
            player.rating = 1000.0
            player.save()

    def exists(self, player_id):
        return self.connection.Player.find_one({'player_id': player_id}) is not None
