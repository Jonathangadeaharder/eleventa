# Eleventa POS - Backend

A Python backend for a Point of Sale (POS) system.

## Setup

1.  Clone the repository.
2.  Create a virtual environment: `python -m venv venv`
3.  Activate the virtual environment:
    *   Windows: `.\venv\Scripts\activate`
    *   Linux/macOS: `source venv/bin/activate`
4.  Install dependencies: `pip install -r requirements.txt`

## Running the Application

Run the main application script:

```bash
python main.py
```

## Running Tests

To run all tests (unit, integration, repository):

```bash
python -m pytest
```

This command will automatically discover and run all tests in the `tests` directory using the configuration in `pytest.ini`. The database fixtures are set up to ensure proper isolation between tests.

## Database Migrations (Alembic)

This project uses Alembic for database schema migrations.

*   **Generate a new migration:** `alembic revision --autogenerate -m "Description of changes"`
*   **Apply migrations:** `alembic upgrade head`

## Project Structure

*   `core/`: Core domain logic (domain models in `core/models/`, services in `core/services/`, and business rule interfaces).
*   `infrastructure/`: Implementation details for persistence (e.g., `infrastructure/persistence/sqlite/` for SQLite ORM models and repositories) and other external integrations.
*   `ui/`: User interface components, views, and dialogs (using PySide6/Qt).
*   `scripts/`: Utility and helper scripts for development or operational tasks.
*   `tests/`: Contains all tests (unit, integration, UI). Test structure mirrors the application structure (e.g., `tests/core`, `tests/ui`).
*   `alembic/`: Database migration scripts managed by Alembic.
*   `main.py`: Main application entry point.
*   `config.py`: Root configuration for the application.
*   `requirements.txt`: Main application dependencies.
*   `requirements-dev.txt`: Development and testing dependencies.
*   `alembic.ini`: Alembic configuration file.
*   `pytest.ini`: Pytest configuration file.
*   `.gitignore`: Specifies intentionally untracked files that Git should ignore.