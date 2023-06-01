#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Public Facebook-Page to Mastodon Cross-Poster
# Copyright (C) 2020  André Menrath (andre.menrath@posteo.de)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
import pickle
import subprocess
import logging
# import tempfile
from datetime import datetime
from os import path
from facebook_scraper import get_posts
from mastodon import Mastodon
# from mastodon.Mastodon import MastodonAPIError, MastodonNetworkError, MastodonRatelimitError, MastodonUnauthorizedError
from vendor import split_tweet

logging.basicConfig(filename='mastaface.log',level=logging.ERROR)

# Global variables
database_filename = 'database.pkl'
config_filename = 'config.json'
mastodon_character_limit_default = 500

logging.info('Execute mastaface at ' + datetime.now().strftime("%Y-%m-%d, %H:%M:%S") )

try: # Open config file and verify it is valid json
    with open(config_filename, 'r') as f:
        logging.debug('found config: ' + config_filename)
        try:
            config = json.load(f)
        except:
            logging.error('Config file in ' + config_filename + ' is not valid json')
except:
        logging.error('Config file ' + config_filename + ' not found')
        exit
logging.debug('Loaded config from ' + config_filename)

# Get history-database
# Check if database file exists
if path.exists(database_filename):
    logging.debug('Found briding-history-database at ' + database_filename)
    try:
        database = pickle.load( open( database_filename, "rb" ) )
    except Exception as e:
        logging.error(e)
    logging.debug('Loaded bridging-history-database')
else:
    logging.warning('No bridging-history-database found at' + database_filename)
    # initialize database
    database = {}

for bridge in config['bridges']:
    try: # Generate Mastodon Python API Object
        mastodon = Mastodon(
            access_token = bridge['mastodon_access_token'],
            api_base_url = bridge['mastodon_api_base_url']
        )
        # Get first=last facebook page
        posts = get_posts(bridge['facebook_page'], pages=3)
        # Extract very last post
        post = list(posts)[0]
        # Split-up facebook post into tweets according to character limit, and reserve room for links
        if post['link']:
            mastodon_character_limit = mastodon_character_limit_default - 30
        else:
            mastodon_character_limit = mastodon_character_limit_default
        # Define text to too
        if len(post['post_text']) == 0: # for example when only a link is shared
            post_text = post['shared_text'] # usally the title of a shared link
        else:
            post_text = post['post_text'] 
        toots_text = split_tweet.split_tweet(post_text, mastodon_character_limit)
        # Check if current bridge already exists in database
        if bridge['facebook_page'] not in database:
            database[bridge['facebook_page']] = {}
            database[bridge['facebook_page']]['last_post_id'] = None
            database[bridge['facebook_page']]['last_edited'] = None
            database[bridge['facebook_page']]['mastodon_statuses'] = None
        # Check if there is a new post, or the last one has been edited
        if post['time'] != database[bridge['facebook_page']]['last_edited']:
            if post['post_id'] == database[bridge['facebook_page']]['last_post_id']:
                logging.info('Last bridged post of https://www.facebook.com/' + bridge['facebook_page'] + ' has been updated')
                # Last post has been updated, so first delete the old toot
                for status in database[bridge['facebook_page']]['mastodon_statuses']:
                    Mastodon.status_delete(status['id'])
                    logging.info('Deleted post ' + str(status['id']) + ' on mastodon because of facebook edit')
            else:
                logging.info('New post on https://www.facebook.com/' + bridge['facebook_page'] + ' found')   
            statuses = None
            statuses = []
            # Upload images if one at least exists and no youtube video is to be linked
            if post['image'] and not (type(post['link']) == str and post['link'].find('youtu') != -1):
                medias = []
                for image in post['images']:
                    # Using curl is necessary, because facebook's secure-image is very restrictive
                    subprocess.run(['curl', image, '--output', 'tmp.jpg',
                                "-H", 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:75.0) Gecko/20100101 Firefox/75.0',
                                "-H", 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                                "-H", 'Accept-Language: de,en-US;q=0.7,en;q=0.3', "--compressed" ,
                                "-H", 'DNT: 1',
                                "-H", 'Connection: keep-alive', "-H", 'Upgrade-Insecure-Requests: 1'])
                    media = mastodon.media_post("tmp.jpg")
                    medias.append(media)

            # unwrapp media ids from list of media_posts (dicts) to list of media ids (list of strings)
            media_ids = []
            for media in medias:
                media_ids.append(media['id'])

            # Toot
            # If post is too long, split it into main-toot and non-listed replies.
            is_main_toot = True
            for toot_text in toots_text:
                if post['link'] and is_main_toot and (toot_text.find(post['link']) == -1):
                    toot = toot_text + '\n\n' + post['link'].replace('https://youtu.be/', 'https://invidious.ggc-project.de/')
                else:
                    toot = toot_text.replace('https://youtu.be/', 'https://invidious.ggc-project.de/')
                if is_main_toot:
                    if post['image']:
                        statuses.append(mastodon.status_post(toot, media_ids=media_ids))
                    else:
                        statuses.append(mastodon.status_post(toot))
                    is_main_toot = False
                    logging.info('Bridged post ' + str(post['post_id']) + ' to ' + str(statuses[-1]['id']) )
                else:
                    statuses.append(mastodon.status_post(toot, in_reply_to_id = statuses[-1], visibility = 'unlisted'))
            # If database structure for current bridge does not exist yet, initialize it.
            database[bridge['facebook_page']] = {}
            database[bridge['facebook_page']]['last_post_id'] = post['post_id']
            database[bridge['facebook_page']]['last_edited'] = post['time']
            database[bridge['facebook_page']]['mastodon_statuses'] = statuses
        else:
            logging.info('No updates to bridge for https://www.facebook.com/'+ bridge['facebook_page'] )
    except Exception as e:
        logging.error('Error bridging' + bridge['facebook_page'])
        logging.debug(e)
        continue
    
# Save database to file
try:
    pickle.dump(database, open(database_filename, "wb" ))
    logging.debug('updated bridging-history-database at' + database_filename)
except Exception as e:
    logging.error('error writing bridging-history-database at' + database_filename)
    logging.debug(print(e))
