"# RAPILite" 
This async wrapper is pretty simple to use

To get started;

`pip install RAPILite`

From here we can simply import the class ready for use

`from reddit import Reddit`

---
Both the regular class instantiation and classmethod require a call to `.load()` afterwards
to actually fetch the data from Reddit, making this `load` call a coroutine

---
The `.load()` coroutine can also take a `comments` kwarg as a bool, setting this to True fetches the comments for all 
posts the url could see (multiple posts for a subreddit link, just one for a specific link)

---
Example 1;
Reddit as a regular object;
```
askreddit = await Reddit('https://www.reddit.com/r/AskReddit').load()
for post in askreddit.posts:
    # each item here is a PostData object with attributes reflecting what the api returns
    # and timestamps converted to datetime objects
    # there are many attributes here like `post.comments`, `post.author`, etc.
```
---

Example 2;
Reddit as a regular object from a classmethod;
```
# this is almost identical to above, just a classmethod shortcut
vids = await Reddit.from_sub('videos').load()
for post in vids.posts:
  ...
```
---
Attributes and their types;
```
Many of the below objects are populated entirely from reddit's api, so will have names/attributes useless to end users

reddit = await Reddit.from_sub('AskReddit').load(comments=True)
reddit.posts: collections.deque[PostData]
reddit.posts[n] is a PostData object with the below attributes

PostData;
    .all_awardings: deque[Award], Award objects representing awards on the post
    .url: str, the url tied to that post by the author, NOT the link for the post itself
    .full_url: str, the actual post's url
    .edited: bool, if the post is edited or not, if this is True then .edited_utc will exist
    .comments: deque[Comment], Comment objects representing comments
    .over_18: bool, is the post marked nsfw
    .pinned: bool, is the post pinned
    etc.

Comment;
    .replies: deque[Comment], replies to this specific comment
    .score: int, upvotes - downvotes
    .author: str, authors name
    .body: str, the content of the comment
    etc.

Award;
    .coin_price: int, amount of reddit coins spent on the award
    .coin_reward: int, amount of reddit coins given to the author of the post/comment
    .name: str, name of the award
    .description: str, description of the award
    .icon_url: str, url of the image for the award
    .count: int, number of times this award has been given
    etc.
```
---
