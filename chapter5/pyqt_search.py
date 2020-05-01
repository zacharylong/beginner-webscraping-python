try:
    from PySide.QtGui import *
    from PySide.QtCore import *
    from PySide.QtWebKit import *
except ImportError:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    # from PyQt5.QtWebKit import * // deprecated
    from PyQt5.QtWidgets import *
    from PyQt5.QtWebEngineWidgets import *

app = QCoreApplication([])
webview = QWebEngineView()
loop = QEventLoop()
webview.loadFinished().connect(loop.quit)
webview.load(QUrl('http://example.webscraping.com/search'))
loop.exec_()
webview.show()
frame = webview.page().mainFrame()
frame.findFirstElement('#search_term').setAttribute('value', '.')
frame.findFirstElement('#page_size option:checked').setPlainText('1000')
frame.findFirstElement('#search').evaluateJavaScript('this.click()')
# app.exec_() ## uncomment and this will become a blocking event

elements = None
while not elements:
    app.processEvents()
    elements = frame.findAllElements('#results a')

countries = [e.toPlainText().strip() for e in elements]
print(countries)

