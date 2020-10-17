"# RAPILite" 

**R**eddit **API** **Lite** (lite since it doesn't use authorization and is readonly)

This async wrapper is pretty simple to use

To get started;

`pip install RAPILite`

From here we can simply import the class ready for use

`from reddit import Reddit`

---
Both the regular class instantiation and classmethod require a call to `.load()` afterwards
to actually fetch the data from Reddit, making this `load` call a coroutine

The `.load()` coroutine can also take a `comments` kwarg as a bool, setting this to True fetches the comments for all 
posts the url could see (multiple posts for a subreddit link, just one for a specific link)
---
Example;
```
from reddit import Reddit
reddit = await Reddit.from_sub('memes').load()
---
#is functionally the same as
---
from reddit import Reddit
reddit = await Reddit('https://reddit.com/r/memes/hot').load()
---
#there are also options for timeframe filtering
reddit = await Reddit.from_sub('pics', method='top', timeframe='all').load()
# the above is functionally the same as
reddit = await Reddit('https:reddit.com/r/memes/top/?t=all').load()

for post in reddit.posts:
    #post is now a PostData object and has attributes as listed below
    post.comments[0] #this will be a Comment object, as represented below

    post.source_image #this will be an Image object, representing
                      #the post's image/gif/video, if applicable

    bytesio_obj = await post.fetch_media(raw_bytes=False)
    # now can do stuff with the io.BytesIO instance, such as image manipulation, etc.
```

```
# You can also change subs with the same object, no need to make new variables
from reddit import Reddit
reddit = await Reddit.from_sub('videos').load()
# do stuff with those posts
# now time to change subreddit
new_sub = await reddit.change_sub('pics', method='top', timeframe='all')
# now we're looking at r/pics, sorted by top of all time, simple
```

---
Attributes and their types;
```
Many of the below objects are populated entirely from reddit's api, so will have names/attributes useless to end users

reddit = await Reddit.from_sub('AskReddit').load(comments=True)
reddit.posts: collections.deque[PostData]
reddit.posts[n] is a PostData object with the below attributes

PostData;
    .title: str, title of the post
    .subreddit: str, name of the subreddit the post belongs to
    .author: str, name of the author of the post
    .selftext: str, selftext of the post, can be considered the main body of text
    .url: str, the url tied to that post by the author, NOT the link for the post itself
    .full_url: str, the actual post's url
    .edited: bool, if the post is edited or not, if this is True then .edited_utc will exist
    .comments: deque[Comment], Comment objects representing comments
    .score: int, front facing score of the post, usually the same as upvotes
    .ups: int, number of upvotes reddit is showing for the post
    .created: datetime.datetime, local (local to the author) creation time of the post
    .created_at: datetime.datetime, UTC+-0 creation time of the post
    .permalink: str, the url of the post after and including 'r/'; eg, "r/memes/comments/..."
    .source_image: Image, an object containing data about the image/video/gif of the post

    .approved_at_utc: Optional[datetime.datetime], time (in UTC+-0) that the post was approved, if applicable
    .saved: bool, this should always be False since this module can't interact with reddit
    .clicked: bool, should also always be False, same as .saved
    .hidden: bool, should always be False, same as .saved
    .pinned: bool, is the post pinned, should be False

    .gilded: int, number of Reddit Gold awards recieved
    .top_awarded_type: str, name of the top award recieved
    .total_awards_recieved: int, number of awards the post recieved
    .all_awardings: deque[Award], Award objects representing awards on the post

    .subreddit_name_prefixed: str, subreddit name with 'r/' prefix
    .subreddit_subscribers: int, number of subscribers the subreddit has
    .thumbnail_height: int, height of the thumbnail
    .thumbnail_width: int, width of the thumbnail
    .thumbnail: str, thumbnail of the post's media, if applicable
    .upvote_ratio: float, ratio of ups and downs to 2 decimal places
    .over_18: bool, is the post marked nsfw
    .spoiler: bool, is the post marked as a spoiler
    .media: MediaInfo, contains data about a posted image/gif, etc.
    
    await fetch_image(*raw_bytes=True):
        if raw_bytes is True;
            returns the bytes of the image/gif/video of the post, if applicable
        otherwise returns an io.BytesIO object of the same data for quality of life

Comment;
    .body: str, the content of the comment
    .author: str, the comment author's name
    .score: int, forward facing score of the post
    .created: datetime.datetime, local (to the author) time of the comment
    .created_utc: datetime.datetime: UTC+-0 time of the comment

    .total_awards_received: int, number of awards on the comment
    .gilded: int, number of Reddit Gold awards on the comment
    .all_awardings: deque[Award], a deque of Award objects representing reddit awards
    
    .edited: bool, is the comment edited
    .is_submitter: bool, is the commenter the author of the post
    .stickied: bool, is the comment stickied to the top of the post
    .replies: deque[Comment], replies to this specific comment

    
Award;
    .name: str, name of the award
    .count: int, number of times this award has been given
    .description: str, description of the award

    .coin_price: int, amount of reddit coins spent on the award
    .coin_reward: int, amount of reddit coins given to the author of the post/comment
    .days_of_premium: int, number of days of premium given to the author of the post/comment

    .icon_url: str, url of the image for the award
    .static_icon_url: str, url of the image for the award

    .icon_height: int, height of the icon image
    .static_icon_height: int, height of the icon image

    .icon_width: int, width of the icon image
    .static_icon_width: int, width of the icon image

    .icon_format: str, format of the award's icon

Image;
    .url: str, the url of the source image of the post
    .width: int, width of the image
    .height: int, height of the image

```
---
