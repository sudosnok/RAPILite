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
from collections import deque
import io
from typing import Union

from reddit import utils


class ResponseData:
    def __init__(self, target, sub, data: dict, cs: ClientSession):
        self._data = data
        self._cs = cs
        self.sub = sub
        self.posts = deque()

        if target == 'post':
            data = data[0]['data']['children'][0]['data']
            self.posts.append(PostData(data))
        else:
            data = data['data']['children']
            subreddit = SubredditData(sub, data, self._cs)
            self.posts.extend(subreddit.posts)
            pass


class SubredditData:
    def __init__(self, sub, data: dict, cs: ClientSession):
        self.sub = sub
        self._cs = cs
        self._data = data
        self.posts = deque()

        for post in self._data:
            self.posts.append(PostData(post['data'], self._cs))

    def __repr__(self) -> str:
        return "<{0.__class__.__name__} sub='{0.sub}' posts={1}>".format(self, len(self.posts))


class PostData:
    def __init__(self, data: dict, cs: ClientSession):
        self._data = data
        self._cs = cs
        self.comments = deque()

        containers = ['all_awardings', ]
        datetimes = ['created_utc', 'edited_utc', 'banned_at_utc', ]

        for key, value in data.items():
            if key in containers:
                setattr(self, key, deque())
            elif key in datetimes:
                if value:
                    setattr(self, key, utils.parse_dt(value))
                else:
                    setattr(self, key, value)
            else:
                setattr(self, key, value)

        # for ease of use
        self.full_url = 'https://www.reddit.com' + self.permalink

        # media info
        self._media = media = MediaInfo(data)
        self.source_image = None or media.source_image
        self.images = media.images

        # filling out the Award objects
        awards = self._data['all_awardings']
        if awards:
            for award in awards:
                self.all_awardings.append(Award(award))

    def __repr__(self) -> str:
        return "<{0.__class__.__name__} author='{0.author}' title='{0.title}' num_comments={0.num_comments}>".format(self)

    async def fetch_image(self, *, raw_bytes: bool = True) -> Union[bytes, io.BytesIO]:
        """
        Returns raw bytes or a BytesIO object of a specific image in the post
        :param bool raw_bytes:  whether to return a bytes object or an io.BytesIO object
        :return: Union[bytes, io.BytesIO]
        """

        res = await self._cs.get(self.media.url)
        image = await res.read()

        if raw_bytes:
            return image

        out = io.BytesIO(image)
        out.seek(0)
        return out


class Comment:
    def __init__(self, data: dict):
        self._data = data

        containers = ['all_awardings', 'replies']
        datetimes = ['approved_at_utc', 'banned_at_utc', 'created_utc', 'edited_utc']
        for key, value in data.items():
            if key in containers:
                setattr(self, key, deque())
            elif key in datetimes:
                if value:
                    setattr(self, key, utils.parse_dt(value))
                else:
                    setattr(self, key, value)
            else:
                setattr(self, key, value)

        try:
            if data['replies']:
                self._replies_data = replies = data['replies']['data']['children']
                for reply in replies:
                    self.replies.append(self.__class__(reply['data']))
        except KeyError:
            pass

        try:
            awards = self._data['all_awardings']
            if awards:
                for award in awards:
                    self.all_awardings.append(Award(award))
        except KeyError:
            pass

    def __repr__(self) -> str:
        if self.body:
            if len(self.body) >= 40:
                body = self.body[:40]
            else:
                body = self.body
            if hasattr(self, 'author'):
                return "<{0.__class__.__name__} author='{0.author}' body='{1}' score={0.score}>".format(self, body)
            return "<{0.__class__.__name__} author='[deleted]' body='{1}' score={0.score}>".format(self, body)
        return "<{0.__class__.__name__} author='{0.author}' body=None score={0.score}".format(self)

    def __str__(self) -> str:
        return self.body


class MediaInfo:
    def __init__(self, data: dict):
        self._data = data
        self.title = self.provider = None

        self.url = data.get('url_overridden_by_dest', data.get('url', None))
        self.images = deque()
        self.source_image = None

        if data['thumbnail'] != 'self':
            self.thumbnail = data['thumbnail']

        try:
            post_hint = data['post_hint']
        except KeyError:
            post_hint = None

        if post_hint == 'image':
            self._get_image_info()

        if post_hint == 'rich:video':
            self._get_video_info()

    def __str__(self) -> str:
        return self.url

    def __repr__(self) -> str:
        return "<{0.__class__.__name__} title='{0.title}' provider='{0.provider}' url='{0.url}'>".format(self)

    def _get_image_info(self):
        data: dict = self._data
        self.source_image = Image(data['preview']['images'][0]['source'])

    def _get_video_info(self):
        data: dict = self._data
        try:  # if its gfycat or youtube
            secure = data['secure_media']['oembed']
            if secure['author'] == 'Gfycat':
                # definitely gfycat
                self.provider = secure['author']
                self.url = data['url_overridden_by_dest']
            else:
                # is youtube
                self.provider = secure['provider_name']
                self.title = secure['title']
                self.author = secure['author']
                pass
        except (KeyError, IndexError):
            # is reddit domain
            self.provider = 'reddit'
            self.url = data['url_overridden_by_dest']


class Image:
    def __init__(self, data: dict):
        self._data = data
        self.width = data['width']
        self.height = data['height']
        self.url = data['url']


class Award:
    def __init__(self, data: dict):
        self._data = data

        for key, value in data.items():
            setattr(self, key, value)

    def __repr__(self) -> str:
        return "<{0.__class__.__name__} name='{0.name}' description='{0.description}' count={0.count}>".format(self)

