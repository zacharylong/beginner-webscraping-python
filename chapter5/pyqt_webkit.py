import lxml.html


try:
    from PySide.QtGui import *
    from PySide.QtCore import *
    from PySide.QtWebKit import *
except ImportError:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5 import QtWebEngineWidgets
    from PyQt5 import QtWebEngine, QtWebEngineCore
    from PyQt5.QtWidgets import QApplication


url = 'http://example.webscraping.com/dynamic'
app = QApplication([])
webview = QWebView()
loop = QEventLoop()
webview.loadFinished.connect(loop.quit)
webview.load(QUrl(url))
loop.exec_()
html = webview.page().mainFrame().toHtml()
tree = lxml.html.fromstring(html)
print(tree.cssselect('#result')[0].text_content())
