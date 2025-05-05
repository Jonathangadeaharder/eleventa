@echo off
echo Running all repository tests individually...
echo.

echo Running User Repository Tests...
python -m pytest tests/infrastructure/persistence/test_user_repository.py -v
if %errorlevel% neq 0 (
    echo User Repository Tests failed!
    exit /b %errorlevel%
)
echo.

echo Running Department Repository Tests...
python -m pytest tests/infrastructure/persistence/test_department_repository.py -v
if %errorlevel% neq 0 (
    echo Department Repository Tests failed!
    exit /b %errorlevel%
)
echo.

echo Running Product Repository Tests...
python -m pytest tests/infrastructure/persistence/test_product_repository.py -v
if %errorlevel% neq 0 (
    echo Product Repository Tests failed!
    exit /b %errorlevel%
)
echo.

echo Running Sale Repository Tests...
python -m pytest tests/infrastructure/persistence/test_sale_repository.py -v
if %errorlevel% neq 0 (
    echo Sale Repository Tests failed!
    exit /b %errorlevel%
)
echo.

echo Running Invoice Repository Tests...
python -m pytest tests/infrastructure/persistence/test_invoice_repository.py -v
if %errorlevel% neq 0 (
    echo Invoice Repository Tests failed!
    exit /b %errorlevel%
)
echo.

echo All repository tests completed successfully! 