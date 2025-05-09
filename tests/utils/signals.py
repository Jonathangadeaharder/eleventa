from PySide6.QtTest import QSignalSpy

def wait_for_signal(sender, signal_name: str, timeout=5000) -> bool:
    spy = QSignalSpy(sender, signal_name)
    return spy.wait(timeout)
