"# RAPILite" 
This async wrapper is pretty simple to use

To get started;

`pip install RAPILite`

From here we can simply import the class ready for use

`from reddit import Reddit`

---

Example 1;
Reddit as an iterator:
```
for post in Reddit('https://reddit.com/r/AskReddit'):
  # post here is a PostData object
  post.title, post.author, post.url
  # post.media will be a MediaInfo object, containing information about the url, provider and title if applicable
  # post.posted_at/edited_at will be a datetime.datetime object in utc
  # post.awards will be a collections.deque of Award objects, with attributes like .name, .url, .price, .count
```

---

Example 2;
Reddit as a regular object;
```
askreddit = Reddit('https://www.reddit.com/r/AskReddit')

askreddit.posts # same as above, a deque of PostData objects
await askreddit.populate_comments()
# now we should have access to the comments from each of the posts in askreddit.posts
for post in askreddit:
  post.comments # this should now be a populated deque of Comment objects for each post
  post.comments[n].awards # a deque of Award objects
```
---

Example 2.5;
Reddit as a regular object from a classmethod;
```
vids = Reddit.from_sub('videos')
for post in vids:
  ...
