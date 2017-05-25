#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = 'HustMeituanBot'
SITENAME = '华科美团点评技术俱乐部'
#SITEURL = '/pages/about/index.html'

THEME = 'theme'

PATH = 'content'

TIMEZONE = 'Asia/Shanghai'
DEFAULT_LANG = 'zh'
LOCALE = 'zh_CN.UTF-8'

DATE_FORMATS = {
    'en': (('en_US', 'utf8'), '%a %Y-%b-%d'),
    'zh': (('zh_CN', 'utf8'), '%Y年%b%d日 周%a'),
}

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (('Pelican', 'http://getpelican.com/'),
         ('Python.org', 'http://python.org/'),
         ('Jinja2', 'http://jinja.pocoo.org/'),
         ('You can modify those links in your config file', '#'),)

# Social widget
HEADER_COVER = '/images/bg.jpg'
SOCIAL = (('github', 'https://github.com/HUSTMeituanClub'),
          ('envelope', 'mailto:@hustmeituan.club'))

STATIC_PATHS = ['static',
                'images',
                'extra/favicon.ico',
                'static/CNAME']


DEFAULT_PAGINATION = 10
EXTRA_PATH_METADATA = {
    'static/CNAME': {'path': 'CNAME'},
    'extra/favicon.ico': {'path': 'favicon.ico'}
}

PAGE_URL = 'pages/{slug}'
PAGE_SAVE_AS = 'pages/{slug}/index.html'

MD_EXTENSIONS = [
    'admonition',
    'toc',
    'codehilite(css_class=highlight)',
    'extra',
]
# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True

RELATIVE_URLS = True

DISPLAY_PAGES_ON_MENU = True


MENUITEMS = [('分类', '/categories.html'),
             ('归档','/archives.html'),
             ('作者','/authors.html'),
             ('标签','/tags.html'),
             ('关于', '/pages/about/index.html'),
             ('友链', '/pages/friendlinks/index.html'),
             
             ]

