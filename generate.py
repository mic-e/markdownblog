#!/usr/bin/env python3
import markdown
import os
import itertools
import html
import re
import time
from collections import defaultdict

blogname = 'sftblog'

htmltemplate = open('html.template').read()

indextemplate = open('index.md.template').read()
tagtemplate = open('tag.md.template').read()
authortemplate = open('author.md.template').read()
posttemplate = open('post.md.template').read()


def natural_sort_key(s, regex=re.compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower()
            for text in regex.split(s)]


def markdownescape(s):
    return ''.join('\\%s' % c
                   if c in '\\`*_{}[]()#+-.!'
                   else c
                   for c in s)


def markdownlist(l):
    return '- ' + '\n- '.join(l)


def readfile(fname, *hdr):
    try:
        raw = open(fname).read()
    except:
        raise Exception("%s: cound not read" % fname)

    lines = raw.split('\n')

    for lineno, l in enumerate(lines):
        if l == '':
            break

        k, v = l.split(': ', maxsplit=1)
        k = k.strip().lower()
        v = v.strip()

        for key in hdr:
            if k in key.names:
                try:
                    key.parse(v)
                except Exception as e:
                    raise Exception("%s:%d: %s"
                                    % (fname, lineno, e.args[0])) from e
                break
        else:
            raise Exception("%s:%d: unknown key %s" % (fname, lineno, k))

    for key in hdr:
        try:
            key.check()
        except Exception as e:
            raise Exception("%s: header invalid: %s"
                            % (fname, e.args[0])) from e

    return {key.names[0]: key for key in hdr}, '\n'.join(lines[lineno + 1:])


class Key:
    """
    a key in a markdown header
    """
    def __init__(self, *names, argc=1, default=None, listsep=None,
                 allowemptylines=False, testfun=None):
        """
        names:
            list of names for this key
        argc:
            either an integer, or one of '?*+'
        default:
            if not None, an empty value list is replaced by this.
            may be a list of values.
        listsep:
            if not None, multiple items can be specified in one line,
            separated by listsep (example: ',')
        allowemptylines:
            if True, lines may contain no value(s
        testfun:
            a callable that is invoked for every value, and may raise
            an exception if the value is unfit
        """
        self.names = names
        self.argc = argc
        self.default = default
        self.listsep = listsep
        self.allowemptylines = allowemptylines
        self.testfun = testfun

        self.vals = []

        self.minvals = 0
        self.maxvals = float('inf')
        if type(argc) == int:
            if argc == 1:
                self.expected = "one value"
            else:
                self.expected = "%d values" % argc
            self.minvals = self.maxvals = argc
        elif argc == '?':
            self.expected = "at most one value"
            self.maxvals = 1
        elif argc == '*':
            self.expected = "any number of values"
        elif argc == '+':
            self.expected = "at least one value"
            self.minvals = 1
        else:
            raise Exception("illegal arg count specifier: %s" % argc)

    def parse(self, v):
        """
        parses a value from one header line, and appends the values to vals
        """
        if self.listsep is None:
            vals = [v]
        else:
            vals = v.split(self.listsep)

        vals = [v.strip() for v in vals if v.strip()]

        if not vals and not allowempty:
            raise Exception("empty value")

        for v in vals:
            if self.testfun is not None:
                self.testfun(v)
            self.vals.append(v)

    def check(self):
        # apply default value(s)
        if not self.vals and default is not None:
            if type(default) == list:
                self.vals = list(default)
            else:
                self.vals = [default]

        if not self.minvals <= len(self.vals) <= self.maxvals:
            raise Exception("expected %s, but got %s"
                            % (self.expected, self.vals))

        if self.maxvals == 1:
            if self.vals:
                self.val = self.vals[0]
            else:
                self.val = None


def datetestfun(v):
    try:
        time.strptime(v, '%Y-%m-%d')
    except Exception as e:
        raise Exception("date is not YYYY-MM-DD: %s" % v) from e


def identifiertestfun(v, name="identifier"):
    if not v.isidentifier():
        raise Exception("not a valid %s: %s" % (name, v))


class Post:
    def __init__(self, fname):
        self.fname = fname

        hdrkeys = [Key('title'),
                   Key('authors', 'author', listsep=',', argc='+',
                       testfun=lambda v: identifiertestfun(v, "author name")),
                   Key('date', testfun=datetestfun),
                   Key('tags', 'tag', listsep=',', argc='*',
                       testfun=lambda v: identifiertestfun(v, "tag name"))]

        hdr, self.content = readfile(fname, *hdrkeys)

        self.title = hdr['title'].val
        self.date = hdr['date'].val
        self.authors = hdr['authors'].vals
        self.tags = hdr['tags'].vals

        self.url = '%s.html' % self.fname.rstrip('.md')
        self.escapedtitle = markdownescape(self.title)
        self.listingstring = "%s [%s](%s) by %s; tags: %s" % (
            self.date,
            self.escapedtitle,
            self.url,
            ', '.join('[%s](author-%s.html)' % (a, a) for a in self.authors),
            ', '.join('[%s](tag-%s.html)' % (t, t) for t in self.tags))

tags = defaultdict(lambda: [])
authors = defaultdict(lambda: [])
posts = []
for f in reversed(sorted(os.listdir('.'), key=natural_sort_key)):
    if not f.endswith('.md') or not f.startswith('post-'):
        continue

    post = Post(f)
    posts.append(post)
    for tag in post.tags:
        tags[tag].append(post)
    for author in post.authors:
        authors[author].append(post)


output = {}


try:
    import pygments
    extensions = ['markdown.extensions.codehilite']
except:
    print('pygments not found; code highlighting disabled.')
    extensions = []


def addoutput(filename, htmltitle, markdowntemplate, **formatting):
    content = markdowntemplate.format(**formatting)
    htmlcontent = markdown.markdown(content, extensions=['markdown.extensions.codehilite'])
    page = htmltemplate.format(title=html.escape(formatting['title']),
                               content=htmlcontent)
    output[filename] = page


tlist = ', '.join("[%s](tag-%s.html)" % (t, t) for t in sorted(tags))
alist = ', '.join("[%s](author-%s.html)" % (a, a) for a in sorted(authors))

# generate index
try:
    indexcontent = open('index.md').read()
except:
    indexcontent = ''

addoutput('index.html', blogname, indextemplate,
          title="%s: index" % blogname,
          content=indexcontent,
          tags=tlist,
          authors=alist,
          posts=markdownlist(p.listingstring for p in posts))

# generate tags
for tag in tags:
    try:
        content = open('tag-%s.md' % tag).read()
    except:
        content = ''

    addoutput('tag-%s.html' % tag, "%s: tag: %s" % (blogname, tag),
              tagtemplate, title=tag, content=content,
              posts=markdownlist(p.listingstring for p in tags[tag]))

# generate authors
for author in authors:
    try:
        content = open('author-%s.md' % tag).read()
    except:
        content = ''

    addoutput('author-%s.html' % author, "%s: author: %s" % (blogname, author),
              authortemplate, title=author, content=content,
              posts=markdownlist(p.listingstring for p in authors[author]))

# generate posts
for post in posts:
    alist = ', '.join("[%s](author-%s.html)" % (a, a) for a in post.authors)
    tlist = ', '.join("[%s](tag-%s.html)" % (t, t) for t in post.tags)

    addoutput(post.url, "%s: %s" % (blogname, post.title), posttemplate,
              title=post.title, authors=alist, date=post.date, tags=tlist,
              content=post.content)

# write generated data
for fname, data in output.items():
    if os.path.isfile(fname):
        with open(fname) as f:
            if f.read() == data:
                continue
        print("updating %s" % fname)
    else:
        print("creating %s" % fname)

    open(fname, 'w').write(data)

existinghtmls = {f for f in os.listdir('.') if f.endswith('.html')}

for fname in existinghtmls - set(output):
    print("deleting %s" % fname)
    os.unlink(fname)
