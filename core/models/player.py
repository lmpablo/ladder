PlayerSchema = {
    'player_id': {
        'type': 'string',
        'empty': False,
        'required': True
    },
    'first_name': {
        'type': 'string'
    },
    'rating': {
        'type': 'number'
    },
    'k_factor': {
        'type': 'integer'
    },
    'basic_stats': {
        'type': 'dict',
        'schema': {
            'last_game_played': {
                'type': 'datetime'
            },
            'num_games_played': {
                'type': 'integer'
            }
        }
    },
    'other_stats': {
        'type': 'dict'
    }
}
