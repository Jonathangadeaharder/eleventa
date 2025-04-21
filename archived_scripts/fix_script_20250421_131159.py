import
re
with open('tests/ui/dialogs/test_select_customer_dialog.py', 'r') as f:
    content = f.read()
pattern = re.compile(r'def test_customer_selection_and_accept\(select_customer_dialog, test_customers, monkeypatch\):')
content = re.sub(pattern, 'def test_customer_selection_and_accept(select_customer_dialog, test_customers, monkeypatch, qtbot):', content)
with open('tests/ui/dialogs/test_select_customer_dialog.py', 'w') as f:
    f.write(content)
