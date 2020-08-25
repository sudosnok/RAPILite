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

from io import BytesIO
from aiohttp import ClientSession
from datetime import datetime
from collections import deque
from typing import Union

from reddit import utils, types


BASE_URL = 'https://www.reddit.com/r/'


class Reddit:
    def __init__(self, url: str, *, cs: ClientSession = None):
        self.last_update = datetime.utcnow()
        self.url = url
        self._cs = cs or ClientSession()
        self.posts = deque()

        is_post, self.sub, self.method = utils.is_post(url)
        if is_post:
            self.target = 'post'
        else:
            self.target = 'subreddit'

    async def _get_response(self, *, override_url: Union[str, None] = None) -> dict:
        url = override_url or self.url
        res = await self._cs.get(url)
        if res.content_type == 'application/json':
            return await res.json()
        elif res.content_type == 'text/html':
            res = await self._cs.get(url + '.json')
            return await res.json()

    def _load_posts(self) -> None:
        if not self.posts:
            self.posts = self._response.posts

    @classmethod
    def from_sub(cls, sub: str, *, method: str = 'hot', cs: ClientSession = None):
        """
        Shortcut to allow users to get a picture of the top posts in a given sub with a given filter method
        :param sub: The subreddit to load from
        :type sub: str
        :param method: The sort method of said subreddit
        :type method: str
        :param cs: Option to supply your own ClientSession if one is already running
        :type cs: ClientSession

        :return Reddit:
        """
        return cls("{}{}/{}".format(BASE_URL, sub, method), cs=cs)

    async def load_comments(self) -> None:
        """
        This makes a call to the API for comment information in each post the url can see

        :return None:
        """
        if not self.posts:
            self._load_posts()
        for post in self.posts:
            post: types.PostData
            # noinspection PyUnresolvedReferences
            data = await self._get_response(override_url=post.full_url)
            comments = deque(data[1]['data']['children'])
            for comment in comments:
                # noinspection PyUnresolvedReferences
                post.comments.append(types.Comment(comment['data']))

    async def fetch_media(self, image: types.Image, *, to_bytes: bool = False) -> Union[BytesIO, bytes]:
        """
        this expects an Image object, as found in post.images
        :param types.Image image: Image object
        :param bool to_bytes: Determines if bytes or BytesIO are returned

        :return Union[BytesIO, bytes]:
        """
        res = await self._cs.get(image.url)

        if res.status == 200:
            out = await res.read()
        elif res.status == 403:
            raise types.ForbiddenUrl("The url tied to this image returns 403 Forbidden; \n{0}".format(image.url))
        else:
            raise NotImplemented

        if to_bytes:
            return out

        out = BytesIO(out)
        out.seek(0)
        return out

    async def load(self, *, comments: bool = True):
        """
        This makes the call to Reddit's API to fetch post & comment information
        :param comments: whether or not to fetch comment data for all posts the original url can see
        :type comments: bool
        :return Reddit:
        """
        # decided to do the api call here instead of in ResponseData's init to avoid asyncio magic
        self._response = types.ResponseData(self.target, self.sub, await self._get_response())
        self._load_posts()
        if comments:
            await self.load_comments()
        return self

