PANDOC := pandoc
PANDOC_OPTS := -H include/style.html -H include/rsslink.html

content: \
	public/index.html \
	public/blog/a-new-blog-using-pandoc-and-make.html \
	public/blog/automatically-secure-nginx-with-letsencrypt-and-ansible.html \
	public/blog.rss

public/blog.rss: $(wildcard content/*.md) scripts/buildrss.py
	python3 scripts/buildrss.py -o public/blog.rss

public/%.html: content/%.md $(BASES)
	$(PANDOC) $< $(PANDOC_OPTS) -s -o $@
