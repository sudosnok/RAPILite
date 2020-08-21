"""
MIT License

Copyright (c) 2020 - sudosnok

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

import asyncio
from aiohttp import ClientSession
from typing import Coroutine
from datetime import datetime
from collections import deque

import utils


class NotPopulated(Exception):
    pass


class ResponseData:
    def __init__(self, target, sub, coro: Coroutine):
        self.sub = sub
        self.posts = deque()
        loop = asyncio.get_event_loop()
        self._data = data = loop.run_until_complete(coro)

        if target == 'post':
            print(data.keys())
            data = data['data']['children'][0]['data']
            self.posts.append(PostData(data))
        else:
            data = data['data']['children']
            subreddit = SubredditData(sub, data)
            self.posts.extend(subreddit.posts)
            pass


class SubredditData:
    def __init__(self, sub, data: dict):
        self.sub = sub
        self._data = data
        self.posts = deque()

        self.populate_posts()

    def populate_posts(self):
        for post in self._data:
            self.posts.append(PostData(post['data']))

    def __repr__(self) -> str:
        return "<{0.__class__.__name__} sub={0.sub} posts={1}>".format(self, len(self.posts))


class PostData:
    def __init__(self, data: dict):
        self._data = data

        # post data
        self.sub = data['subreddit']
        self.title = data['title']
        self.author = data['author']
        self.url = r"https://www.reddit.com" + data['permalink']
        self.posted_at = utils.parse_dt(float(data['created_utc']))
        try:
            self.edited_at = utils.parse_dt(float(data['edited_utc']))
        except KeyError:
            self.edited_at = None

        # social stuffs
        self.upvote_ratio = data['upvote_ratio']
        self.num_comments = data['num_comments']
        self.score = data['score']
        self.awards = deque()
        self.total_awards = data['total_awards_received']
        self.score_hidden = data['hide_score']

        # relating to visibility
        self.locked = data['locked']
        self.quarantined = data['quarantine']
        self.nsfw = data['over_18']
        self.archived = data['archived']
        self.spoiler = data['spoiler']
        self.stickied = data['stickied']

        # media info
        self.media = MediaInfo(data)

        # comments
        self.comments = deque()

        self.populate_awards()

    def populate_awards(self):
        awards = self._data['all_awardings']
        if awards:
            for award in awards:
                self.awards.append(Award(award))

    def __repr__(self) -> str:
        return "<{0.__class__.__name__} author={0.author} title={0.title} num_comments={0.num_comments}>".format(self)


class Comment:
    def __init__(self, data: dict):
        self._data = data

        self.text = data['body']
        self.author = data['author']
        self.is_submitter = data['is_submitter']
        self.posted_at = utils.parse_dt(data['created_utc'])
        if isinstance(data['edited'], float):
            self.edited_at = utils.parse_dt(data['edited'])
            self.is_edited = True
        else:
            self.is_edited = False
        self.stickied = data['stickied']

        self.score = data['score']
        self.awards = deque()
        self.total_awards = data['total_awards_received']

        self.replies = deque()
        self._replies_data = replies = data['replies']['data']['children']
        for reply in replies:
            self.replies.append(self.__class__(reply['data']))

        self.populate_awards()

    def __repr__(self) -> str:
        return "<{0.__class__.__name__} author={0.author} text={0.text} score={0.score}>".format(self)

    def __str__(self) -> str:
        return self.text

    def populate_awards(self):
        awards = self._data['all_awardings']
        if awards:
            for award in awards:
                self.awards.append(Award(award))


class MediaInfo:
    def __init__(self, data: dict):
        self._data = data
        self.title = self.provider = self.url = None

        if not data['secure_media']:
            return

        try:    # if its gfycat or youtube
            secure = data['secure_media']['oembed']
            if secure['author'] == 'Gfycat':
                # definitely gfycat
                self.provider = secure['author']
                self.url = data['url']
            else:
                # is youtube
                self.provider = secure['provider_name']
                self.title = secure['title']
                self.author = secure['author']
                pass
        except (KeyError, IndexError):
            # is reddit domain
            self.provider = 'reddit'
            self.url = data['url']

        if data['thumbnail'] != 'self':
            self.thumbnail = data['thumbnail']

    def __str__(self) -> str:
        return self.url

    def __repr__(self) -> str:
        return "<{0.__class__.__name__} title={0.title} provider={0.provider} url={0.url}>".format(self)


class Award:
    def __init__(self, data: dict):
        self._data = data
        self.name = data['name']
        self.description = data['description']
        self.count = data['count']

        self.icon_url = data['icon_url']
        self.icon_fmt = data['icon_format']
        self.icon_dim = (data['icon_width'], data['icon_height'])

        self.days_premium = data['days_of_premium']
        self.price = data['coin_price']
        self.reward = data['coin_reward']

    def __repr__(self) -> str:
        return "<{0.__class__.__name__} name={0.name} description={0.description} count={0.count}>".format(self)


BASE_URL = 'https://www.reddit.com/r/'


class Reddit:
    def __init__(self, url: str, *, cs: ClientSession = None):
        self._start(url, cs=cs)

    def __iter__(self):
        if not self.posts:
            self._populate_posts()
        self._current_post = self.posts[0]
        return self

    def __next__(self):
        post = self._current_post
        try:
            self._current_post = self.posts[self.posts.index(post) + 1]
            return post
        except IndexError:
            raise StopIteration

    def _start(self, url: str, cs: ClientSession = None):
        self.url = url
        self._cs = cs or ClientSession()
        self.posts = deque()

        is_post, self.sub, self.method = utils.is_post(url)
        if is_post:
            target = 'post'
        else:
            target = 'subreddit'

        self._response = ResponseData(target, self.sub, self._get_response())
        self._populate_posts()
        self._last_update = datetime.utcnow()

    @classmethod
    def from_sub(cls, sub: str, *, method: str = 'hot', cs: ClientSession = None):
        return cls("{}{}/{}".format(BASE_URL, sub, method), cs=cs)

    async def populate_comments(self):
        if not self.posts:
            self._populate_posts()
        for post in self.posts:
            post: PostData
            res = await self._cs.get(post.url)
            data = await res.json()
            comments = deque(data[1]['data']['children'])
            for comment in comments:
                post.comments.append(Comment(comment['data']))

    async def _get_response(self) -> dict:
        res = await self._cs.get(self.url)
        if res.content_type == 'application/json':
            return await res.json()
        elif res.content_type == 'text/html':
            res = await self._cs.get(self.url + '.json')
            return await res.json()

    def _populate_posts(self):
        if not self.posts:
            self.posts = self._response.posts


"""TODO: put types and the two utils functions into their own files"""
"""TODO: fix the get_event_loop mess in ResponseData"""
