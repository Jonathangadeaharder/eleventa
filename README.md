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

*   `core/`: Core domain logic, models, services, interfaces.
*   `infrastructure/`: Database persistence (SQLite), external service integrations.
*   `ui/`: User interface components (potentially using PySide/Qt).
*   `tests/`: Unit, integration, and infrastructure tests.
*   `main.py`: Main application entry point.
*   `requirements.txt`: Project dependencies.
*   `alembic/`: Alembic migration scripts.
*   `alembic.ini`: Alembic configuration.
*   `pytest.ini`: Pytest configuration.