PANDOC := pandoc
BASES := include/style.html

content: public/index.html public/blog/a-new-blog-using-pandoc-and-make.html

# `public/` is not checked into git, this is used
# to make sure it is always present before running
# pandoc on a clean checkout or after removing `public`.
public public/blog:
	mkdir public
	mkdir public/blog

public/%.html: content/%.md public public/blog $(BASES)
	cat $(BASES) $< | $(PANDOC) -s -o $@
