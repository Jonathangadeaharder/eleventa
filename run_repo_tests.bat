@echo off
echo Running Repository Tests...

rem Change to the root directory
cd /d "%~dp0"

rem Define the path to Python and pytest
set PYTHON=venv\Scripts\python.exe
set PYTEST=%PYTHON% -m pytest

rem Run tests with output to console
echo Testing calculate_profit_for_period...
%PYTEST% tests/infrastructure/persistence/test_sale_repository.py::test_calculate_profit_for_period -v

echo Testing get_sales_summary_by_period...
%PYTEST% tests/infrastructure/persistence/test_sale_repository.py::test_get_sales_summary_by_period -v

echo Testing all sale repository tests...
%PYTEST% tests/infrastructure/persistence/test_sale_repository.py -v

echo Done. 