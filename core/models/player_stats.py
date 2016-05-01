from mongokit import Document
from config import DB_NAME
import datetime


class PlayerStats(Document):
    __database__ = DB_NAME
    __collection__ = 'player_stats'
    use_dot_notation = True

    structure = {
        'player_id': basestring,
        'num_games_played': {
            'total': int,
            'won': int,
            'lost': int
        },
        'longest_win_streak': int,
        'longest_lose_streak': int,
        'ppg': float,
        'win_ppg': float,
        'lose_ppg': float,
        'ppg_diff': float,
        'win_ppg_diff': float,
        'lose_ppg_diff': float,
        'current_streak': {
            'type': basestring,
            'streak': int
        },
        'match_ups': [{
            'opp_id': basestring,
            'opp_slack_name': basestring,
            'opp_profile_picture': basestring,
            'last_played_against': datetime.datetime,
            'games_played_against': int,
            'games_won_against': int,
            'games_lost_against': int,
            'ppg_against': float,
            'pr_win_against': float
        }]
    }

    required_fields = ['player_id']

    default_values = {
        'num_games_played.total': 0,
        'num_games_played.won': 0,
        'num_games_played.lost': 0,
        'longest_win_streak': 0,
        'longest_lose_streak': 0,
        'ppg': 0.0,
        'win_ppg': 0.0,
        'lose_ppg': 0.0,
        'ppg_diff': 0.0,
        'win_ppg_diff': 0.0,
        'lose_ppg_diff': 0.0,
        'match_ups': [],
        'current_streak.type': 'win',
        'current_streak.streak': 0
    }

    indexes = [
        {
            'fields': ['player_id'],
            'unique': True
        }
    ]

