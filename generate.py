#!/usr/bin/env python3
import markdown
import os
import itertools
import html
import re
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


def error(msg):
    print(msg)
    exit(1)


class Post:
    def gethdrval(self, lineno, kexpected):
        if len(self.raw) <= lineno:
            error("%s: header incomplete" % self.fname)
        try:
            k, v = l.split(': ', maxsplit=1)
        except:
            error("%s: invalid header line format: %s" % (self.fname, l))

        if k.strip().lower() != kexpected.strip().lower():
            error("%s: expected key: %s, but got %s in line %d"
                % (self.fname, kexpected, k, lineno))

        return v.strip()

    def __init__(self, fname, existingposts):
        self.fname = fname
        self.raw = open("post-%s" % fname).read().split('\n')

        self.title = self.gethdrval(0, 'title')
        self.escapedtitle = markdownescape(self.title)
        self.date = self.gethdrval(1, 'date')
        try:
            time.strptime(self.date, '%Y-%m-%d')
        except:
            error("%s: date is not YYYY-MM-DD: %s" % (self.fname, self.date))
        self.authors = self.gethdrval(2, 'authors').split(', ')
        self.authors = [a.strip() for a in self.authors if a.strip()]
        if not self.authors:
            error("%s: no author given" % self.fname)
        for a in self.authors:
            if not a.isidentifier():
                error("%s: illegal author name: %s" % (self.fname, a))
        self.tags = gethdrval(3, 'tags').split(', ')
        self.tags = [t.strip() for t in self.tags if t.strip()]
        if not tags:
            error("%s: no tags given" % self.fname)
        for t in self.tags:
            if not t.isidentifier():
                error("%s: illegal tag name: %s" % (self.fname, t))
        self.content = '\n'.join(self.raw[4:])

        existingurls = {p.url for p in existingposts}
        self.url = self.title.replace(' ', '-').replace('_', '-')
        self.url = ''.join(c for c in self.url if c.isalnum() or c=='-')
        if self.url in existingurls:
            self.urlhead = self.url
            for i in itertools.count():
                self.url = "%s%d" % (self.urlhead, i)
                if self.url not in existingurls:
                    break

        self.listingstring = "%s [%s](post-%s) by %s; tags: %s" % (
            self.date,
            self.escapedtitle,
            self.url,
            ', '.join('[%s](author-%s)' % a for a in self.authors),
            ', '.join('[%s](tag-%s)' % t for t in self.tags))

        existingposts.append(self)

    def to_html(self):
        pass

tags = defaultdict(lambda: [])
authors = defaultdict(lambda: [])
posts = []
for f in reversed(sorted(os.listdir('.'), key=natural_sort_key)):
    if not f.endswith('.md') or not f.startswith('post-'):
        continue

    post = Post(f, posts)
    for tag in post.tags:
        tags[tag].append(post)
    for author in post.authors:
        authors[author].append(post)


output = {}
def addoutput(filename, markdowntemplate, **formatting):
    content = markdowntemplate.format(**formatting)
    htmlcontent = markdown.markdown(content)
    page = htmltemplate.format(title=html.escape(formatting['title']),
                               content=htmlcontent)
    output[filename] = page


tlist = ', '.join("[%s](tag-%s)" % (t, t) for t in sorted(tags))
alist = ', '.join("[%s](author-%s)" % (a, a) for a in sorted(authors))

# generate index
try:
    indexcontent = open('indexcontent.md').read()
except:
    indexcontent = ''
addoutput('index.html', indextemplate,
          title=blogname,
          content = indexcontent,
          tags=tlist,
          authors=alist,
          posts='\n\n'.join(p.listingstring for p in posts))

# generate tags
for tag in tags:
    try:
        content = open('tag-%s.md' % tag).read()
    except:
        content = ''

    addoutput('tag-%s.html' % tag, tagtemplate,
              title='%s: tag: %s' % (blogname, tag),
              content=content,
              posts='\n\n'.join(p.listingstring for p in tags[tag]))

# generate authors
for author in authors:
    try:
        content = open('author-%s.md' % tag).read()
    except:
        content = ''

    addoutput('author-%s.html' % author, authortemplate,
              title='%s: author: %s' % (blogname, author),
              content=content,
              posts='\n\n'.join(p.listingstring for p in authors[author]))

# generate posts
for post in posts:
    alist = ', '.join("[%s](author-%s)" % (a, a) for a in post.authors)
    tlist = ', '.join("[%s](tag-%s)" % (t, t) for t in post.tags)
    addoutput('post-%s.html' % post.url, posttemplate,
              title='%s: %s' % (blogname, post.title),
              authors=alist,
              tags=tlist,
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
