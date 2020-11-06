# personal website

This repository hosts the source files for my personal website,
https://jchri.st.

My pages are written in
[Markdown](https://daringfireball.net/projects/markdown/), translated to HTML
with [pandoc](https://pandoc.org) using [make](./Makefile), and deployed to the
live server using [Ansible](./deploy.yml). A small [Python
script](./scripts/buildrss.py) compiles the RSS feed.
