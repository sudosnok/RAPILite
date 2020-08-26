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
The `.load()` coroutine can also take a `comments` kwarg as a bool, setting this to false 
drastically improves speed, since no limits are placed on comment loading yet

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
