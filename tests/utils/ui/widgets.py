from PySide6.QtWidgets import QPushButton
from .events import process_events

def find_widget_by_text(parent, widget_type, text):
    for w in parent.findChildren(widget_type):
        if getattr(w, 'text', lambda: None)() == text:
            return w
    return None

def safe_click_button(button):
    if button and callable(getattr(button, 'click', None)):
        button.click()
        process_events()
        return True
    return False
