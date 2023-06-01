forked from https://codeberg.org/linos/mastaface

## Mastaface -  A simple Facebook to Mastodon Bridge

Mastaface scrapes the last post of a public facebook page and bridges it to mastodon.

## Features:
- splits facebook posts with are longer than the character limit into serveral toots (replies)
- checks only for the last post, so if you miss one, you're out of luck
- only cross-posts up to the first four images of a facebook post

Please be sure to get the permission **before** mirroring some facebook site.

## Dependencies
### OS:
- curl
### Python:
- Mastadon.py
- facebook-scraper

## Usage:
Copy ```config.json.example``` to ```config.json``` and adjust it to your needs.
Setup a cronjob to run the script periodically. Timelap must be shorter than minimum time difference between two facebook posts.
