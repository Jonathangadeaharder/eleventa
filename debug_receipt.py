import sys
sys.path.insert(0, '.')
from infrastructure.reporting.document_generator import DocumentPdfGenerator
from decimal import Decimal
from datetime import datetime
import tempfile
import os
import traceback

g = DocumentPdfGenerator()

receipt_data = {
    "receipt_number": "R-001",
    "date": datetime(2024, 1, 15),
    "customer_name": "Test Customer",
    "items": [
        {
            "description": "Product 1",
            "quantity": Decimal('1'),
            "price": Decimal('100.00')
        }
    ],
    "total": Decimal('100.00'),
    "payment_method": "Efectivo"
}

with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
    output_path = tmp_file.name

try:
    print(f"Testing receipt generation with data: {receipt_data}")
    print(f"Output path: {output_path}")
    
    result = g.generate_receipt(receipt_data, output_path)
    
    print(f"Result: {result}")
    print(f"File exists: {os.path.exists(output_path)}")
    
    if os.path.exists(output_path):
        print(f"File size: {os.path.getsize(output_path)}")
    
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
    
finally:
    if os.path.exists(output_path):
        os.unlink(output_path)