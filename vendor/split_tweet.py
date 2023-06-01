# forked from https://github.com/fawkesley/python-tweet-splitter/blob/master/LICENSE.md
#
# The MIT License (MIT)
#
# Copyright (c) 2015 Paul M Furley paul@paulfurley.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software
# and associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, 
# and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial
#     portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from __future__ import unicode_literals


def split_tweet(long_tweet, length=140):
    assert length >= 10

    if len(long_tweet) <= length:
        return [long_tweet]

    words = long_tweet.split(' ')

    return list(_split_tweets(words, length))


def _split_tweets(words, length):
    tweets = list(_generate_split_tweets(words, length))
    assert len(tweets) < 10

    for i, tweet in enumerate(tweets):
        yield '({}/{}) {}'.format(i + 1, len(tweets), tweet[4:])


def _generate_split_tweets(words, length):
    this_tweet = '?/?'

    while True:
        this_tweet += ' ' + words.pop(0)

        if not words:
            break

        if len(this_tweet) + 1 + len(words[0]) > length:
            yield this_tweet
            this_tweet = '?/?'

    yield this_tweet
