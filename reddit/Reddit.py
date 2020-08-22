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

from aiohttp import ClientSession
from datetime import datetime
from collections import deque

from reddit import utils, types


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

        self._response = types.ResponseData(target, self.sub, self._get_response())
        self._populate_posts()
        self._last_update = datetime.utcnow()

    @classmethod
    def from_sub(cls, sub: str, *, method: str = 'hot', cs: ClientSession = None):
        return cls("{}{}/{}".format(BASE_URL, sub, method), cs=cs)

    async def populate_comments(self):
        if not self.posts:
            self._populate_posts()
        for post in self.posts:
            post: types.PostData
            res = await self._cs.get(post.url)
            data = await res.json()
            comments = deque(data[1]['data']['children'])
            for comment in comments:
                post.comments.append(types.Comment(comment['data']))

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
"""TODO: make MediaInfo look for picture data too"""

