import sys
sys.path.insert(0, '.')
from infrastructure.reporting.document_generator import DocumentPdfGenerator
import os
import traceback

g = DocumentPdfGenerator()

# Test the invalid path that should fail
invalid_path = "/invalid/path/that/does/not/exist/file.pdf"
print(f"Testing invalid path: {invalid_path}")

# Convert to absolute path like the method does
abs_path = os.path.abspath(invalid_path)
output_dir = os.path.dirname(abs_path)
print(f"Absolute path: {abs_path}")
print(f"Output directory: {output_dir}")

# Test if directory can be created
try:
    os.makedirs(output_dir, exist_ok=True)
    print(f"Directory creation succeeded: {os.path.exists(output_dir)}")
except Exception as e:
    print(f"Directory creation failed: {e}")

# Test the actual method
sample_data = {'invoice_number': 'A-001'}
try:
    result = g.generate_invoice_pdf(sample_data, [], invalid_path)
    print(f"generate_invoice_pdf result: {result}")
except Exception as e:
    print(f"generate_invoice_pdf failed: {e}")
    traceback.print_exc()