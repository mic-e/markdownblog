*Python Markdown blog* is a script to generate a static blog from a collection of posts in markdown format; it was written for usage with a git post-receive hook.

#### Usage

- Put each post in a file called `post-name.md`
 - Each individual post requires a header of the following format:

            title:   Example post
            date:    2014-09-26
            author:  mic_e
            tags:    example, misc

   followed by an empty line and the post content.
  - Multiple authors and any number of tags may be specified

 - Posts are sorted in descending order of their filenames, so it is advisable to number your files (`post-0-firstpost`, `post-1-mydailyrage`)
- To generate the static pages, or update them, run `./generate`. All generated files will have the `.html` extesion (conveniently blacklisted in `.gitignore`).
- The following pages are generated:
 - `index.html` (lists all authors, tags and posts)
 - `author-*.html` for each author (lists all posts by that author)
 - `tag-*.html` for each tag (lists all posts with that tag)
 - `post-*.html` for each post
- Apart from `post-*.md`, you can optionally use `index.md`, `author-*.md` and `tag-*.md` to provide extra content for those pages
- To auto-generate the blog from a post-receive hook, take a look at [post-receive](post-receive) (command to install: `git show post-receive > hooks/post-receive; chmod +x hooks/post-receive`)

#### Dependencies

- `python3`
- The [python markdown library](https://pypi.python.org/pypi/Markdown)
- Optionally, for code highlighting, [pygments](http://pygments.org/)

#### License

GPLv3 or higher (see [COPYING](COPYING) and [LICENSE](LICENSE))
