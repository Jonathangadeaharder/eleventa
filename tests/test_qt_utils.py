import pytest
from PySide6.QtCore import QTimer
from PySide6.QtNetwork import QNetworkRequest
from tests.utils.network import FakeNetworkAccessManager

def test_wait_for_signal_timer(qtbot):
    timer = QTimer()
    timer.setSingleShot(True)
    timer.start(50)
    with qtbot.waitSignal(timer.timeout, timeout=1000):
        pass

def test_fake_network_access_manager(qtbot):
    mgr = FakeNetworkAccessManager()
    payload = b'{"foo":"bar"}'
    mgr.set_fake_response(payload, status_code=201)

    req = QNetworkRequest("http://example")
    reply = mgr.get(req)

    with qtbot.waitSignal(reply.finished, timeout=1000):
        pass
    got = bytes(reply.readAll())
    assert got == payload
    status = int(reply.attribute(QNetworkRequest.HttpStatusCodeAttribute))
    assert status == 201
