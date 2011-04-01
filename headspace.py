import sys
import json
import logging
from datetime import datetime
import uuid
import urllib
import urlparse
import lxml
import lxml.etree
import time
import hashlib
import os
import mimetypes
from Queue import Queue
from threading import Thread

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, \
    DateTime, Float, and_, or_
from sqlalchemy.orm.collections import column_mapped_collection as column_mapped
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relation, eagerload

from mutagen.mp3 import EasyMP3 as MP3, HeaderNotFoundError

from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.httpexceptions import HTTPException, HTTPNotFound, HTTPBadRequest
from paste.httpserver import serve

logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger(__name__)


class AppURLopener(urllib.FancyURLopener):
    version = 'Mozilla/5.0'

urllib._urlopener = AppURLopener()

Base = declarative_base()
Session = sessionmaker()

generate_uid = lambda: str(uuid.uuid4()).replace('-', '')
xmlify = lambda i: unicode(i).encode('ascii', 'xmlcharrefreplace')


class Status:
    ACTIVE = 1


class Metadata(Base):
    __tablename__ = 'metadata'

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('sources.id'), nullable=False)

    key = Column(String, nullable=False)
    value = Column(String)

    def __repr__(self):
        return '<Metadata(%id: %s -> %s)>' % (self.id, self.key, self.value)


class Source(Base):
    __tablename__ = 'sources'

    id = Column(Integer, primary_key=True)

    status = Column(Integer, nullable=False, default=Status.ACTIVE)
    type = Column(String, nullable=False)
    uid  = Column(String, unique=True, nullable=False, default=generate_uid)
    url  = Column(String, unique=True, nullable=False)

    hash = Column(String)
    size = Column(Integer)

    last_crawl = Column(DateTime, nullable=False)
    last_fetch = Column(DateTime)
    fetch_time = Column(Float)
    last_index = Column(DateTime)

    data_map = relation('Metadata',
                        backref='source',
                        collection_class=column_mapped(Metadata.key),
                        cascade='all')

    data = association_proxy('data_map', 'value')

    def __repr__(self):
        return '<Source(%s: %s)>' % (self.uid, self.url)

    @property
    def filename(self):
        return self.uid + '.' + self.type

    @property
    def dirname(self):
        return os.path.join(*list(self.uid[:3]))

    @property
    def path(self):
        return os.path.join(self.dirname, self.filename)


def command_crawl(options, args):
    'Crawl a site for links'

    num_workers = 10
    queue = Queue()
    crawled = set()
    found = set()
    allowed_domains = set(urlparse.urlsplit(i).netloc for i in args)
    target_mimes = ['audio/mpeg']

    def is_allowed(url):
        return url.netloc in allowed_domains

    def build_link(base, url):
        return urlparse.urlsplit(urlparse.urljoin(base, url))

    def scrape(base, f):
        root = lxml.etree.parse(f, lxml.etree.HTMLParser()).getroot()

        if not root:
            return ()

        links         = (build_link(base, i) for i in root.xpath('//a/@href'))
        allowed_links = (i for i in links if is_allowed(i))
        link_urls     = (i.geturl() for i in allowed_links)
        new_urls      = (i for i in link_urls if i not in crawled)
        return new_urls

    def content_type(f):
        return f.info().getheader('content-type')

    def is_html(f):
        return 'text/html' in content_type(f)

    def is_target(f):
        return content_type(f) in target_mimes

    def crawl(url):
        print 'crawling', url

        f = urllib.urlopen(url)

        if is_target(f):
            print 'found', content_type(f), url
            found.add(url)
        elif is_html(f):
            new_urls = scrape(url, f)

            for new_url in new_urls:
                crawled.add(new_url)
                queue.put(new_url)

    def worker():
        while True:
            url = queue.get()
            crawl(url)
            queue.task_done()

    for i in range(num_workers):
        t = Thread(target=worker)
        t.daemon = True
        t.start()

    for url in args:
        crawled.add(url)
        queue.put(url)

    t1 = time.time()
    queue.join()
    t2 = time.time()

    print 'Crawled %d urls in %.02f seconds' % (len(crawled), t2 - t1)

    for i in found:
        print i


def command_import(options, args):
    'import jsonlines crawl file'

    session = Session()

    default_crawl_time = datetime.fromtimestamp(0)

    for arg in args:
        with open(arg, 'r') as f:
            for line in f:
                data = json.loads(line)

                url = data.get('url') or data.get('src')
                type = data.get('type') or 'mp3'

                source = session.query(Source).filter_by(url=url).first()
                if not source:
                    source = Source(url=url, type=type)
                    session.add(source)

                source.last_crawl = max(source.last_crawl or \
                                            default_crawl_time,
                                        data.get('last_crawl', datetime.now()))

                session.commit()


def hash_data(path):
    sha1 = hashlib.sha1()

    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(128 * sha1.block_size), ''):
            sha1.update(chunk)

    return sha1.hexdigest()


def index_audio(session, path, source):
    # mp3: length bitrate sketchy
    # id3: artist album title date genre tracknumber encoded by

    try:
        mp3 = MP3(path)
    except HeaderNotFoundError, e:
        log.error('Could not index "%s": %s', e, path)
    else:

        items = {'artist': ' '.join(mp3.get('artist', [])) or None,
                 'album': ' '.join(mp3.get('album', [])) or None,
                 'title': ' '.join(mp3.get('title', [])) or None,
                 'date': ' '.join(mp3.get('date', [])) or None,
                 'genre': ' '.join(mp3.get('genre', [])) or None,
                 'tracknumber': ' '.join(mp3.get('tracknumber', [])) or None,
                 'encodedby': ' '.join(mp3.get('encodedby', [])) or None,
                 'length': int(round(mp3.info.length)),
                 'bitrate': mp3.info.bitrate,
                 'sketchy': mp3.info.sketchy }

        for key in items:
            if key not in source.data:
                i = Metadata(source=source, key=key)
                session.add(i)
                source.data_map[key] = i

            source.data[key] = xmlify(items[key]) if items.get(key) else None


def command_fetch(options, args):
    'fetch a list of uids'

    def makedirs(source):
        path = os.path.join('data', source.dirname)
        if not os.path.exists(path):
            os.makedirs(path)

        return path

    def report(num_blocks, block_size, total_blocks):
        print >>sys.stderr, 'num blocks/block_size/total blocks: %s/%s/%s' % \
            (num_blocks, block_size, total_blocks)

    def fetch(source):
        path = os.path.join('data', source.path)
        urllib.urlretrieve(source.url, path, report)
        return path

    session = Session()

    for arg in args:
        source = session.query(Source).filter_by(uid=arg).first()

        if not source:
            log.error('Unknown source %s', arg)
            continue

        makedirs(source)

        t1 = time.time()
        path = fetch(source)
        t2 = time.time()

        delta = t2 - t1
        log.info('Fetched %s in %.04fs', source.url, delta)

        source.last_fetch = datetime.now()
        source.fetch_time = delta
        source.size = os.stat(path).st_size
        source.hash = hash_data(path)

        session.commit()


def command_unfetched(options, args):
    'print a list of unfetched uids'

    session = Session()

    for source in session.query(Source).filter(Source.hash == None):
        print source.uid


# FIXME this is bit of a hack
def command_scan(options, args):
    'index local mp3s'

    def is_audio(path):
        return mimetypes.guess_type(path)[0] == 'audio/mpeg'

    def scan(path):
        for path, dirnames, filenames in os.walk(path):
            for i in filenames:
                cur_path = os.path.abspath(os.path.join(path, i))
                if is_audio(i):
                    yield cur_path

    session = Session()

    for arg in args:
        for path in scan(arg):
            print 'Scanning', path

            # FIXME
            masked = '/home/marc'
            base_url = 'https://lenny.quuux.org/'
            type = 'mp3'

            relpath = os.path.relpath(path, masked)
            url = base_url + relpath.decode('utf-8')

            source = session.query(Source).filter_by(url=url).first()

            if not source:
                source = Source(url=url, type=type)
                session.add(source)

            source.last_crawl = datetime.now()
            source.size = os.stat(path).st_size
            source.hash = hash_data(path)

            index_audio(session, path, source)

            session.commit()


def command_index(options, args):
    'index a list of uids'

    session = Session()
    for arg in args:
        source = session.query(Source).filter_by(uid=arg).first()

        if not source:
            log.error('Unknown source %s', arg)
            continue

        path = os.path.join('data', source.path)

        if not os.path.exists(path):
            log.error('Source %s not fetched', arg)
            continue

        index_audio(session, path, source)
        source.last_index = datetime.now()
        session.commit()


def command_unindexed(options, args):
    'print a list of unindexed uids'

    session = Session()

    query = session.query(Source).filter(and_(Source.hash != None,
                                              ~Source.data_map.any()))
    for source in query:
        print source.uid


def command_seed(options, args):
    'scrape seed links from google'

    def query(q):
        endpoint = 'https://encrypted.google.com/search'
        params = {'q': q, 'num': 100}
        qs = urllib.urlencode(params)
        url = endpoint + '?' + qs
        return urllib.urlopen(url)

    def mp3_query(q):
        return query('intitle:"index of" "parent directory " '   \
                         '"last modified" "size" "description" ' \
                         '"%s" mp3 -html -htm -php -shtml' % q )

    def scrape(f):
        root = lxml.etree.parse(f, lxml.etree.HTMLParser()).getroot()
        return root.xpath('//h3/a/@href')

    for arg in args:
        results = scrape(mp3_query(arg))
        for result in results:
            print result


def command_serve(options, args):
    'start webserver'

    def http_exc(exc, request):
        body = '<html><head><title>%s</title></head>' \
            '<body><h1>%s</h1><p>%s</p></body></html>'
        response = Response(body % (exc.title, exc.title, exc.detail))
        response.status_int = exc.code
        return response

    def search(request):
        session = Session()

        query  = request.GET.get('q')
        offset = int(request.GET.get('offset', 0))
        limit = int(request.GET.get('limit', 10))

        if not query:
            raise HTTPBadRequest('No query given')

        term = lambda k, v: and_(Metadata.key == k,
                                 Metadata.value.like(query + '%'))

        criteria = and_(Source.hash != None,
                        Source.data_map.any(or_(term('title', query),
                                                term('artist', query),
                                                term('album', query))))

        sources = session.query(Source)           \
                         .filter(criteria)        \
                         .options(eagerload('data_map'))

        return {'sources': sources,
                'count': sources.count(),
                'query': query,
                'limit': limit,
                'offset': offset,
                'xhr': request.is_xhr}

    def index(request):
        return {}

    def get_source(request):
        session = Session()

        uid = request.matchdict['uid']
        source = session.query(Source).filter_by(uid=uid).first()

        if not source:
            return HTTPNotFound('Source %s not found' % uid)

        return {'uid': source.uid,
                'type': source.type,
                'url': source.url,
                'hash': source.hash,
                'size': source.size,
                'data': dict(source.data)}

    settings = {'mako.directories': ['templates'],
                'reload_templates': 'true'}

    config = Configurator(settings=settings)

    config.add_view(index, renderer='index.mako')
    config.add_view(search, renderer='search.mako', name='search')
    config.add_route('source', 'source/{uid}', renderer='json',
                     view=get_source)
    config.add_static_view(name='static', path='static')
    config.add_view(http_exc, context=HTTPException)

    app = config.make_wsgi_app()
    serve(app, host='0.0.0.0')


def command_help(options, args):
    'print help message'

    print >>sys.stderr, 'USAGE: %s [options] [command]' % sys.argv[0]
    print >>sys.stderr

    print >>sys.stderr, 'Commands:'
    for command in commands:
        print >>sys.stderr, "% 10s% 40s" % (command, commands[command].__doc__)

is_command = lambda k, v: k.startswith('command_') and callable(v)
commands = dict((k[8:], v) for k, v in globals().items() if is_command(k, v))


def main(options, args):

    engine = create_engine('sqlite:///data/db.sqlite', echo=True)
    Base.metadata.create_all(engine)
    Session.configure(bind=engine)

    if len(args) < 1:
        command_help(options, args)
        return 1

    command = args[0]
    if command not in commands:
        command_help(options, args)
        return 1

    return commands[command](options, args[1:])

if __name__ == '__main__':
    sys.exit(main(None, sys.argv[1:]))
