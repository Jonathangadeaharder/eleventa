from PySide6.QtCore import QTimer, QByteArray, QIODevice
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

class FakeNetworkReply(QNetworkReply):
    def __init__(self, data: bytes, status: int = 200, parent=None):
        super().__init__(parent)
        self._data = QByteArray(data)
        self._read = False
        self.open(QIODevice.OpenModeFlag.ReadOnly)
        self.setHeader(QNetworkRequest.ContentTypeHeader, QByteArray(b"application/json"))
        self.setAttribute(QNetworkRequest.HttpStatusCodeAttribute, status)
        QTimer.singleShot(0, self._emit_ready)

    def abort(self): pass

    def bytesAvailable(self):
        return 0 if self._read else self._data.size()

    def isSequential(self): return True

    def readData(self, maxlen):
        if self._read:
            return b''
        chunk = self._data[:maxlen]
        self._read = True
        return bytes(chunk)

    def readAll(self):
        self._read = True
        return self._data

    def _emit_ready(self):
        self.readyRead.emit()
        self.finished.emit()


class FakeNetworkAccessManager(QNetworkAccessManager):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = QByteArray()
        self._status = 200

    def set_fake_response(self, data: bytes, status_code: int = 200):
        self._data, self._status = QByteArray(data), status_code

    def createRequest(self, op, req, outgoingData=None):
        return FakeNetworkReply(bytes(self._data), self._status, self)
