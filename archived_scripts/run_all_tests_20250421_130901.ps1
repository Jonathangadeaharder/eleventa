# PowerShell script to run integration tests and all other tests separately for robust Qt test isolation

# 1. Run integration tests first (isolated)
pytest -m integration

# 2. Run all other tests (excluding integration)
pytest -m "not integration"
