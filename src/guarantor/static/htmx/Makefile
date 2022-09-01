.PHONY: default
default:
	wget --no-parent -r "https://unpkg.com/browse/htmx.org@1.8.0/dist/"
	mkdir -p ext/
	mv unpkg.com/browse/htmx.org@1.8.0/dist/*.js .
	mv unpkg.com/browse/htmx.org@1.8.0/dist/ext/*.js ext/
	rm -rf unpkg.com/
