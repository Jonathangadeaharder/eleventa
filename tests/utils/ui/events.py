from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QEventLoop

def process_events():
    QApplication.instance().processEvents()

def wait_for(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()

def wait_until(cond, timeout=5000, interval=50):
    import time
    start = time.time()
    while (time.time() - start)*1000 < timeout:
        if cond(): return True
        wait_for(interval)
    return False
