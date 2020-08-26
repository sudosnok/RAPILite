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

from collections import deque

from reddit import utils


class ForbiddenUrl(Exception):
    pass


class ResponseData:
    def __init__(self, target, sub, data: dict):
        self._data = data
        self.sub = sub
        self.posts = deque()

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

        for post in self._data:
            self.posts.append(PostData(post['data']))

    def __repr__(self) -> str:
        return "<{0.__class__.__name__} sub='{0.sub}' posts={1}>".format(self, len(self.posts))


class PostData:
    def __init__(self, data: dict):
        self._data = data
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
        # noinspection PyUnresolvedReferences
        self.full_url = 'https://www.reddit.com' + self.permalink

        # media info
        self.media = media = MediaInfo(data)
        self.source_image = None or media.source_image
        self.images = media.images

        # filling out the Award objects
        awards = self._data['all_awardings']
        if awards:
            for award in awards:
                # noinspection PyUnresolvedReferences
                self.all_awardings.append(Award(award))

    def __repr__(self) -> str:
        return "<{0.__class__.__name__} author='{0.author}' title='{0.title}' num_comments={0.num_comments}>".format(self)


# noinspection PyUnresolvedReferences
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
        if len(self.body) >= 40:
            return "<{0.__class__.__name__} author='{0.author}' text='{1}' score={0.score}>".format(self, self.body[:40])
        return "<{0.__class__.__name__} author='{0.author}' text='{0.body}' score={0.score}>".format(self)

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

        if not data['secure_media']:
            return

        post_hint = data['post_hint']

        if post_hint == 'image':
            self._get_image_info()

        if post_hint == 'rich:video':
            self._get_video_info()

    def __str__(self) -> str:
        return self.url

    def __repr__(self) -> str:
        return "<{0.__class__.__name__} title='{0.title}' provider='{0.provider}' url={0.url}>".format(self)

    def _get_image_info(self):
        data: dict = self._data
        preview = data['preview']
        if preview['enabled']:
            images = preview['images']
            self.source_image = Image(images[0]['source'])
            for image in images[0]['resolutions']:
                try:
                    self.images.append(Image(image))
                except KeyError:
                    break

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

