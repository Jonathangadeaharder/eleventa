#!/bin/bash
echo "Running all repository tests individually..."
echo ""

echo "Running User Repository Tests..."
python -m pytest tests/infrastructure/persistence/test_user_repository.py -v
if [ $? -ne 0 ]; then
    echo "User Repository Tests failed!"
    exit 1
fi
echo ""

echo "Running Department Repository Tests..."
python -m pytest tests/infrastructure/persistence/test_department_repository.py -v
if [ $? -ne 0 ]; then
    echo "Department Repository Tests failed!"
    exit 1
fi
echo ""

echo "Running Product Repository Tests..."
python -m pytest tests/infrastructure/persistence/test_product_repository.py -v
if [ $? -ne 0 ]; then
    echo "Product Repository Tests failed!"
    exit 1
fi
echo ""

echo "Running Sale Repository Tests..."
python -m pytest tests/infrastructure/persistence/test_sale_repository.py -v
if [ $? -ne 0 ]; then
    echo "Sale Repository Tests failed!"
    exit 1
fi
echo ""

echo "Running Invoice Repository Tests..."
python -m pytest tests/infrastructure/persistence/test_invoice_repository.py -v
if [ $? -ne 0 ]; then
    echo "Invoice Repository Tests failed!"
    exit 1
fi
echo ""

echo "All repository tests completed successfully!" 