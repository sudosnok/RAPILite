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
The `.load()` coroutine can also take a `comments` kwarg as a bool, setting this to True entails many api calls to each
post the url could see, potentially taking a minute or more

Its for this reason that you should only set `comments=True` if the url provided was a url to a specific post

Due to the exponentially increasing number of API calls to fetch the whole comment history

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
