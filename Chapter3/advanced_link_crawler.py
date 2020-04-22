from urllib.parse import urljoin
from urllib.error import URLError, HTTPError, ContentTooShortError
import urllib.request
import re
import itertools
from urllib import robotparser
from lxml.html import fromstring
# throttle libs
from urllib.parse import urlparse
import time
from random import choice
import requests

proxy = 'http://myproxy.net:1234'   # example string

class Throttle:
    """
    Add a delay between downloads to the same domain
    """
    def __init__(self, delay):
        # amount of delay between downloads
        self.delay = delay
        # timestamp of when a domain was last accessed
        self.domains = {}

    def wait(self, url):
        domain = urlparse(url).netloc
        last_accessed = self.domains.get(domain)

        if self.delay > 0 and last_accessed is not None:
            sleep_secs = self.delay - (time.time() - last_accessed)
            if sleep_secs > 0:
                # domain has been accessed recently
                # so need to sleep
                time.sleep(sleep_secs)
        # update the last accessed tiem
        self.domains[domain] = time.time()

class Downloader:
    def __init__(self, delay=5, user_agent='wswp', proxies=None, cache={}):
        self.throttle = Throttle(delay)
        self.user_agent = user_agent
        self.proxies = proxies
        self.num_retries = None # set per request
        self.cache = cache

    def __call__(self, url, num_retries=2):
        self.num_retries = num_retries
        try:
            result = self.cache[url]
            print('Loaded from cache:', url)
        except KeyError:
            result = None
        if result and self.num_retries and 500 <= result['code'] < 600:
            # server error so ignore result from cache
            # and re-download
            result = None
        if result is None:
            # result was not loaded from cache
            # so still need to download
            self.throttle.wait(url)
            proxies = choice(self.proxies) if self.proxies else None
            headers = {'User-Agent': self.user_agent}
            result = self.download(url, headers, proxies)
            if self.cache:
                # save result to cache
                self.cache[url] = result
        return result['html']

def download(url, num_retries=2, user_agent='wswp', charset='utf-8', proxy=None):
    """ Download a given url and return page content
        args:
            url (str): URL
        kwargs:
            user_agent (str): user agent (default: wswp)
            charset (str): charset if website does not include one in headers
            proxy (str): proxy url, ex 'http://IP' (default: None)
            num_retries (int): number of retries if a 5xx error is seen (default: 2)
    """
    print('Downloading:', url)
    request = urllib.request.Request(url)
    request.add_header('User-agent', user_agent)
    try:
        if proxy:
            proxy_support = urllib.request.ProxyHandler({'http': proxy})
            opener = urllib.request.build_opener(proxy_support)
            urllib.request.install_opener(opener)
        resp = urllib.request.urlopen(request)
        cs = resp.headers.get_content_charset()
        if not cs:
            cs = charset
        html = resp.read().decode(cs)
    except (URLError, HTTPError, ContentTooShortError) as e:
        print('Download error:', e.reason)
        html = None
        if num_retries > 0:
            if hasattr(e, 'code') and 500 <= e.code < 600:
                # recursively retry 5xx http errors
                return download(url, num_retries - 1)
    return html

def get_robots_parser(robots_url):
    " Return the robots parser object using the robots_url "
    rp = robotparser.RobotFileParser()
    rp.set_url(robots_url)
    rp.read()
    return rp

def get_links(html):
    " Return a list of links (using simple regex matching) from the html content "
    # a regular expression to extract all links from the webpage
    webpage_regex = re.compile("""<a[^>]+href=["'](.*?)["']""", re.IGNORECASE)
    # list of all links from the webpage
    return webpage_regex.findall(html)

def link_crawler(seed_url, link_regex, robots_url=None, user_agent='wswp', proxy=None, delay=3, max_depth=4, scrape_callback=None, num_retries=2, cache={}):
    """ Crawl from the given start URL following  links matched by link_regex. In the current implementation, we do not actually scrapy any information.
    args:
    :param start_url: (str) web site to start crawl
    :param link_regex: (str) regex to match  for links
    kwargs
    :param robots_url: (str) url of the sit's robots.txt (default: start_url + /robots.txt
    :param user_agent: (str) user agent (default: wswp)
    :param proxy: (str) proxy url, ex 'http://IP' (default: none)
    :param delay: (int) seconds to throttle between requests to one domain (default: 3)
    :param max_depth: (int) maximum crawl depth (to avoid traps) (default: 4)
    :param scrape_callback: (function) function to call after each download
    :return:
    """

    crawl_queue = [seed_url]
    # keep track of which URL's have seen before
    seen = {seed_url: 0}
    data = []

    if not robots_url:
        robots_url = '{}/robots.txt'.format(seed_url)
    rp = get_robots(seed_url)
    D = Downloader(delay=delay, user_agent=user_agent, proxies=proxies, cache=cahce)

    while crawl_queue:
        url = crawl_queue.pop()
        # check url passes robots.txt restrictions
        if rp.can_fetch(user_agent, url):
            depth = seen.get(url, 0)
            if depth == max_depth:
                continue
            html = D(url, num_retries=num_retries)
            if not html:
                continue

            # TODO: add actual data scraping here
            # filter for links matching our regular expression
            if scrape_callback:
                data.extend(scrape_callback(url, html) or [])

            for link in get_links(html):
                if re.match(link_regex, link):
                    abs_link = urljoin(start_url, link)
                    if abs_link not in seen:
                        seen[abs_link] = depth + 1
                        crawl_queue.append(abs_link)
    else:
        print('Blocked by robots.txt:', url)

def scrape_callback(url, html):
    fields = ('area', 'population', 'iso', 'country', 'capital',
              'continent', 'tld','currency_code', 'currency_name',
              'phone', 'postal_code_format', 'postal_code_regex',
              'languages', 'neighbours')
    if re.search('/view/', url):
        tree = fromstring(html)
        all_rows = [
            tree.xpath('//tr[@id="places_%s__row"]/td[@class="w2p_fw"]' % field)[0].text_content()
            for field in fields]
        print(url, all_rows)


def crawl_sitemap(url):
    # download the sitemap file
    sitemap = download(url)
    # extract the sitemap links
    links = re.findall('<loc>(.*?)</loc>', sitemap)
    # download each link
    for link in links:
        html = download(link)
        # scrape html here
        # ...

def crawl_site(url, max_errors=5):
    for page in itertools.count(1):
        pg_url = '{}{}'.format(url, page)
        html = download(pg_url)
        if html is None:
            num_errors += 1
            if num_errors == max_errors:
                # max errors reached, exit loop
                break
        else:
            num_errors = 0
            # success - can scrape






