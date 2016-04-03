MatchSchema = {
    'match_id': {
        'type': 'string',
        'required': True,
        'empty': False
    },
    'timestamp': {
        'type': 'datetime',
        'required': True
    },
    'winner': {
        'type': 'string'
    },
    'participants': {
        'type': 'list',
        'schema': {
            'type': 'dict',
            'schema':{
                'player_id': {
                    'type': 'string',
                    'required': True
                },
                'score': {
                    'type': 'integer'
                }
            }
        }
    }
}
