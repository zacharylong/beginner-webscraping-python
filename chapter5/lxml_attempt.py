from lxml.html import fromstring
from chapter3.downloader import Downloader

D = Downloader()
html = D('http://example.webscraping.com/search')
tree = fromstring(html)
tree.cssselect('div#results a')