import requests
from pymongo import MongoClient
import argparse


def main(slack_token, db):
    users = requests.get('https://slack.com/api/users.list?token={}'.format(slack_token)).json()

    collected = {}
    deleted_users = []

    for user in users['members']:
        user_profile = user.get('profile')

        user_id = user['id']
        deleted = user.get('deleted', False)
        slack_name = user.get('name', '')
        real_name = user.get('real_name', '')
        profile_picture = user_profile.get('image_512', user_profile.get('image_256'))

        if deleted:
            deleted_users.append(user_id)
        else:
            collected[user_id] = {
                'player_id': user_id,
                'slack_name': slack_name,
                'real_name': real_name,
                'profile_picture': profile_picture
            }

    # this might introduce problems with recalculation
    # for du in deleted_users:
    #     print db['players'].remove({'player_id': du})

    for player in db['players'].find():
        info = collected.get(player['player_id'])
        if info:
            del info['player_id']
            fq = {'player_id': player['player_id']}
            uq = {'$set': info}
            db['players'].update(fq, uq)
        else:
            print "Couldn't find any info for {} - {}".format(player['player_id'], player['real_name'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', required=True)
    parser.add_argument('--token', required=True)
    args = parser.parse_args()

    db = MongoClient()[args.db]
    main(args.token, db)
