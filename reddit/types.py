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
from typing import Coroutine
from collections import deque

from reddit import utils


class ForbiddenUrl(Exception):
    pass


class ResponseData:
    def __init__(self, target, sub, coro: Coroutine):
        self.sub = sub
        self.posts = deque()

        try: # if an event loop is running, make a task and schedule it
            loop = asyncio.get_running_loop()
            task = loop.create_task(coro)
            loop.run_until_complete(task)
            self._data = data = task.result()
        except RuntimeError:  # get_running_loop will raise RuntimeError, so we'll use some other magic
            new_loop = asyncio.new_event_loop()  # could refactor this down but dont want to lose clarity
            task = new_loop.create_task(coro)    # that this loop is created solely for this task
            self._data = data = new_loop.run_until_complete(task)
            if task.done():
                new_loop.close()

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

        self._populate_posts()

    def _populate_posts(self):
        for post in self._data:
            self.posts.append(PostData(post['data']))

    def __repr__(self) -> str:
        return "<{0.__class__.__name__} sub='{0.sub}' posts={1}>".format(self, len(self.posts))


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
        self.source_image = None or self.media._source_image
        self.images = self.media.images

        # comments
        self.comments = deque()

        self._populate_awards()

    def _populate_awards(self):
        awards = self._data['all_awardings']
        if awards:
            for award in awards:
                self.awards.append(Award(award))

    def __repr__(self) -> str:
        return "<{0.__class__.__name__} author='{0.author}' title='{0.title}' num_comments={0.num_comments}>".format(self)


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
        return "<{0.__class__.__name__} author='{0.author}' text='{0.text}' score={0.score}>".format(self)

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
        self.title = self.provider = None
        self.url = data['url_overridden_by_dest']
        self.images = deque()
        self._source_image = None

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
            self._source_image = Image(images[0]['source'])
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
        return "<{0.__class__.__name__} name='{0.name}' description='{0.description}' count={0.count}>".format(self)

