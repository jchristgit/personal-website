---
title: A new blog using pandoc and make
keywords:
  - blog
  - posts
date: June 6, 2019
---

After letting it sit there for a while, I figured that it's time to brush up my
website from the odd setup that I had on there. Namely, the old tech stack was:

- Python & Django to serve posts and provide an Admin interface to edit posts on
- gunicorn as the WSGI application server
- Docker for deployment
- nginx as the reverse proxy

If you think about it, three of the four components here are not really needed,
given that the site is purely static. Therefore, it was time to check out static
site generators.

After trying out Hugo, I figured I might as well make my own. After all,
[pandoc](https://pandoc.org) exists and has always been a perfect document
converter. `make` is used for building the website. My Makefile knowledge is
near zero but this is a good opportunity to learn it.

The Makefile used to build this website:

```makefile
PANDOC := pandoc
BASES := include/style.html

content: public/index.html public/blog/new-blog.html

# `public/` is not checked into git, this is used
# to make sure it is always present before running
# pandoc on a clean checkout or after removing `public`.
public public/blog:
	mkdir public
	mkdir public/blog

public/%.html: content/%.md public public/blog $(BASES)
	cat $(BASES) $< | $(PANDOC) -s -o $@
```

The nice thing here is that it only rebuilds what it needs to rebuild when it
needs to rebuild. For instance, updating this post and calling `:make` in vim
only results in make running `pandoc` for this single file. Updating
`include/style.html`, as another example, will rebuild all posts.

Of course, this isn't a complete solution to all the problems that static site
generators aim to solve. For instance, the blog post table of contents in the
index page is currently being updated manually.

Some of the CSS is also taken from [here](https://bestmotherfucking.website/),
which looks a lot better than the weird CSS I wrote for the old website.

The next steps are deploying it via Ansible and linking to content by hash (an
idea of Joe Armstrong).

<!-- vim: set textwidth=80 sw=2 ts=2: -->
