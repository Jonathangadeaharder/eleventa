import sys
sys.path.insert(0, '.')
from infrastructure.reporting.document_generator import DocumentPdfGenerator
import tempfile
import os

g = DocumentPdfGenerator()

# Test with incomplete data - only invoice_number
incomplete_data = {
    "invoice_number": "A-0001-00000123"
    # Missing other required fields
}
incomplete_items = []

with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
    output_path = tmp_file.name

try:
    print(f"Testing with incomplete data: {incomplete_data}")
    print(f"Items: {incomplete_items}")
    
    result = g.generate_invoice_pdf(incomplete_data, incomplete_items, output_path)
    
    print(f"Result: {result}")
    print(f"File exists: {os.path.exists(output_path)}")
    
    if os.path.exists(output_path):
        print(f"File size: {os.path.getsize(output_path)}")
    
finally:
    if os.path.exists(output_path):
        os.unlink(output_path)