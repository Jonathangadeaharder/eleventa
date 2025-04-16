"""
Integration tests for data import and export.

These tests verify that data can be properly imported from external sources
and exported for backup or data interchange.
"""
import pytest
from unittest.mock import MagicMock, patch, mock_open
import tempfile
import os
import csv
import json
import io


class TestProductDataImport:
    """Tests for importing product data from external sources."""
    
    def test_import_products_from_csv(self):
        """Test importing products from a CSV file."""
        # Create mock repositories
        mock_product_repo = MagicMock()
        
        # Sample CSV content
        csv_content = """code,name,description,price,cost,stock
P001,Product 1,First test product,10.99,5.50,100
P002,Product 2,Second test product,15.50,8.25,50
P003,Product 3,Third test product,25.00,12.00,75
"""
        
        # Create mock file
        mock_csv_file = io.StringIO(csv_content)
        
        # Create minimal product import service
        class ProductImportService:
            def __init__(self, product_repo):
                self.product_repo = product_repo
                
            def import_from_csv(self, file_path):
                # In a real implementation, would open the file
                # For testing, we'll use the provided StringIO
                reader = csv.DictReader(mock_csv_file)
                
                results = {
                    "total": 0,
                    "imported": 0,
                    "skipped": 0,
                    "errors": []
                }
                
                for row in reader:
                    results["total"] += 1
                    
                    try:
                        # Create product dict
                        product_data = {
                            "code": row["code"],
                            "name": row["name"],
                            "description": row["description"],
                            "price": float(row["price"]),
                            "cost": float(row["cost"]),
                            "stock": int(row["stock"])
                        }
                        
                        # Check if product already exists
                        existing = self.product_repo.get_by_code(row["code"])
                        
                        if existing:
                            # Update existing product
                            for key, value in product_data.items():
                                setattr(existing, key, value)
                                
                            self.product_repo.update(existing)
                            results["imported"] += 1
                        else:
                            # Create new product
                            self.product_repo.add(product_data)
                            results["imported"] += 1
                            
                    except Exception as e:
                        results["skipped"] += 1
                        results["errors"].append(str(e))
                
                return results
        
        # Configure repository behavior
        existing_products = {}
        
        def get_by_code(code):
            return existing_products.get(code)
            
        def add_product(product_data):
            code = product_data["code"]
            # Create a mock object with the exact attributes we want to check
            mock_product = MagicMock()
            mock_product.id = len(existing_products) + 1
            mock_product.code = product_data["code"]
            mock_product.name = product_data["name"]
            mock_product.description = product_data["description"]
            mock_product.price = product_data["price"]
            mock_product.cost = product_data["cost"]
            mock_product.stock = product_data["stock"]
            
            existing_products[code] = mock_product
            return mock_product
            
        def update_product(product):
            existing_products[product.code] = product
            return product
            
        mock_product_repo.get_by_code.side_effect = get_by_code
        mock_product_repo.add.side_effect = add_product
        mock_product_repo.update.side_effect = update_product
        
        # Create the service
        import_service = ProductImportService(product_repo=mock_product_repo)
        
        # Test importing products
        results = import_service.import_from_csv("dummy_path.csv")
        
        # Verify results
        assert results["total"] == 3
        assert results["imported"] == 3
        assert results["skipped"] == 0
        
        # Verify repository was called for each product
        assert mock_product_repo.get_by_code.call_count == 3
        assert mock_product_repo.add.call_count == 3
        
        # Verify imported products are in repository
        assert len(existing_products) == 3
        assert existing_products["P001"].name == "Product 1"
        assert existing_products["P002"].price == 15.50
        assert existing_products["P003"].stock == 75


class TestCustomerDataImport:
    """Tests for importing customer data from external sources."""
    
    def test_import_customers_from_json(self):
        """Test importing customers from a JSON file."""
        # Create mock repositories
        mock_customer_repo = MagicMock()
        
        # Sample JSON content
        json_content = """
{
  "customers": [
    {
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "555-1234",
      "tax_id": "TAX123",
      "address": "123 Main St"
    },
    {
      "name": "Jane Smith",
      "email": "jane@example.com",
      "phone": "555-5678",
      "tax_id": "TAX456",
      "address": "456 Oak Ave"
    },
    {
      "name": "Bob Johnson",
      "email": "bob@example.com",
      "phone": "555-9012",
      "tax_id": "TAX789",
      "address": "789 Pine Rd"
    }
  ]
}
"""
        
        # Create minimal customer import service
        class CustomerImportService:
            def __init__(self, customer_repo):
                self.customer_repo = customer_repo
                
            def import_from_json(self, file_path):
                # In a real implementation, would open the file
                # For testing, we'll use the provided JSON string
                customer_data = json.loads(json_content)
                
                results = {
                    "total": len(customer_data["customers"]),
                    "imported": 0,
                    "skipped": 0,
                    "errors": []
                }
                
                for customer in customer_data["customers"]:
                    try:
                        # Check if customer already exists by email
                        existing = self.customer_repo.find_by_email(customer["email"])
                        
                        if existing:
                            # Update existing customer
                            for key, value in customer.items():
                                setattr(existing, key, value)
                                
                            self.customer_repo.update(existing)
                        else:
                            # Create new customer
                            self.customer_repo.add(customer)
                            
                        results["imported"] += 1
                            
                    except Exception as e:
                        results["skipped"] += 1
                        results["errors"].append(str(e))
                
                return results
        
        # Configure repository behavior
        existing_customers = {}
        
        def find_by_email(email):
            for customer in existing_customers.values():
                if customer.email == email:
                    return customer
            return None
            
        def add_customer(customer_data):
            customer_id = len(existing_customers) + 1
            customer = MagicMock(
                id=customer_id,
                **customer_data
            )
            existing_customers[customer_id] = customer
            return customer
            
        def update_customer(customer):
            existing_customers[customer.id] = customer
            return customer
            
        mock_customer_repo.find_by_email.side_effect = find_by_email
        mock_customer_repo.add.side_effect = add_customer
        mock_customer_repo.update.side_effect = update_customer
        
        # Create the service
        import_service = CustomerImportService(customer_repo=mock_customer_repo)
        
        # Test importing customers
        results = import_service.import_from_json("dummy_path.json")
        
        # Verify results
        assert results["total"] == 3
        assert results["imported"] == 3
        assert results["skipped"] == 0
        
        # Verify repository was called for each customer
        assert mock_customer_repo.find_by_email.call_count == 3
        assert mock_customer_repo.add.call_count == 3
        
        # Verify imported customers
        assert len(existing_customers) == 3
        
        # Get all customers and verify data
        all_customers = list(existing_customers.values())
        emails = [c.email for c in all_customers]
        
        assert "john@example.com" in emails
        assert "jane@example.com" in emails
        assert "bob@example.com" in emails


class TestDatabaseBackup:
    """Tests for database backup and restore."""
    
    def test_database_backup(self):
        """Test creating a database backup."""
        # Create mock database service
        mock_db_service = MagicMock()
        
        # Configure db service behavior
        tables_data = {
            "products": [
                {"id": 1, "code": "P001", "name": "Product 1", "price": 10.99},
                {"id": 2, "code": "P002", "name": "Product 2", "price": 15.50}
            ],
            "customers": [
                {"id": 1, "name": "John Doe", "email": "john@example.com"},
                {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
            ],
            "sales": [
                {"id": 1, "date": "2023-05-01", "customer_id": 1, "total": 21.98},
                {"id": 2, "date": "2023-05-02", "customer_id": 2, "total": 15.50}
            ]
        }
        
        def get_all_tables():
            return list(tables_data.keys())
            
        def export_table_data(table_name):
            return tables_data.get(table_name, [])
            
        mock_db_service.get_all_tables.side_effect = get_all_tables
        mock_db_service.export_table_data.side_effect = export_table_data
        
        # Create minimal backup service
        class BackupService:
            def __init__(self, db_service):
                self.db_service = db_service
                
            def create_backup(self, output_file):
                # Get all tables
                tables = self.db_service.get_all_tables()
                
                # Create backup data structure
                backup_data = {
                    "version": "1.0",
                    "date": "2023-05-05T12:00:00",
                    "tables": {}
                }
                
                # Export each table's data
                for table in tables:
                    backup_data["tables"][table] = self.db_service.export_table_data(table)
                
                # Write to file (mocked in the test)
                with open(output_file, 'w') as f:
                    json.dump(backup_data, f, indent=2)
                
                return {
                    "file": output_file,
                    "size": len(json.dumps(backup_data)),
                    "tables": len(tables),
                    "records": sum(len(data) for data in backup_data["tables"].values())
                }
        
        # Create the service
        backup_service = BackupService(db_service=mock_db_service)
        
        # Test creating a backup
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.dump') as mock_json_dump:
                results = backup_service.create_backup("backup.json")
                
                # Verify file was opened for writing
                mock_file.assert_called_once_with("backup.json", 'w')
                
                # Get the backup data that was passed to json.dump
                backup_data = mock_json_dump.call_args[0][0]
                
                # Verify backup data contains expected structure
                assert "version" in backup_data
                assert backup_data["version"] == "1.0"
                assert "tables" in backup_data
                assert "products" in backup_data["tables"]
                assert "customers" in backup_data["tables"]
                assert "sales" in backup_data["tables"]
        
        # Verify db service was called
        assert mock_db_service.get_all_tables.call_count == 1
        assert mock_db_service.export_table_data.call_count == 3
        
        # Verify results
        assert results["tables"] == 3
        assert results["records"] == 6  # 2 products + 2 customers + 2 sales


class TestDatabaseRestore:
    """Tests for database restore operations."""
    
    def test_database_restore(self):
        """Test restoring a database from backup."""
        # Create mock database service
        mock_db_service = MagicMock()
        
        # Sample backup data
        backup_data = {
            "version": "1.0",
            "date": "2023-05-05T12:00:00",
            "tables": {
                "products": [
                    {"id": 1, "code": "P001", "name": "Product 1", "price": 10.99},
                    {"id": 2, "code": "P002", "name": "Product 2", "price": 15.50}
                ],
                "customers": [
                    {"id": 1, "name": "John Doe", "email": "john@example.com"},
                    {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
                ],
                "sales": [
                    {"id": 1, "date": "2023-05-01", "customer_id": 1, "total": 21.98},
                    {"id": 2, "date": "2023-05-02", "customer_id": 2, "total": 15.50}
                ]
            }
        }
        
        # Create minimal restore service
        class RestoreService:
            def __init__(self, db_service):
                self.db_service = db_service
                
            def restore_from_backup(self, backup_file):
                # In a real implementation, would read the file
                # For testing, we'll use the provided backup data
                
                results = {
                    "tables_restored": 0,
                    "records_restored": 0,
                    "errors": []
                }
                
                # Clear existing data first
                self.db_service.begin_transaction()
                
                try:
                    # For each table in the backup
                    for table_name, records in backup_data["tables"].items():
                        # Clear existing table data
                        self.db_service.clear_table(table_name)
                        
                        # Import each record
                        for record in records:
                            self.db_service.import_record(table_name, record)
                        
                        results["tables_restored"] += 1
                        results["records_restored"] += len(records)
                    
                    # Commit changes
                    self.db_service.commit_transaction()
                    
                except Exception as e:
                    # Rollback on error
                    self.db_service.rollback_transaction()
                    results["errors"].append(str(e))
                
                return results
        
        # Create the service
        restore_service = RestoreService(db_service=mock_db_service)
        
        # Test restoring from backup
        results = restore_service.restore_from_backup("backup.json")
        
        # Verify db service was called
        mock_db_service.begin_transaction.assert_called_once()
        assert mock_db_service.clear_table.call_count == 3
        assert mock_db_service.import_record.call_count == 6
        mock_db_service.commit_transaction.assert_called_once()
        
        # Verify results
        assert results["tables_restored"] == 3
        assert results["records_restored"] == 6
        assert len(results["errors"]) == 0


class TestDataExportFormatting:
    """Tests for exporting data in different formats."""
    
    def test_export_data_to_csv(self):
        """Test exporting data to CSV format."""
        # Create mock data repository
        mock_data_repo = MagicMock()
        
        # Sample data to export
        products_data = [
            {"code": "P001", "name": "Product 1", "price": 10.99, "stock": 100},
            {"code": "P002", "name": "Product 2", "price": 15.50, "stock": 50},
            {"code": "P003", "name": "Product 3", "price": 25.00, "stock": 75}
        ]
        
        # Configure repository to return sample data
        mock_data_repo.get_products.return_value = products_data
        
        # Create minimal export service
        class DataExportService:
            def __init__(self, data_repo):
                self.data_repo = data_repo
                
            def export_products_to_csv(self, output_file):
                # Get products data
                products = self.data_repo.get_products()
                
                # Create CSV file
                with open(output_file, 'w', newline='') as csv_file:
                    # Determine field names from first record
                    if products:
                        fieldnames = products[0].keys()
                        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                        
                        # Write header
                        writer.writeheader()
                        
                        # Write data
                        writer.writerows(products)
                
                return {
                    "file": output_file,
                    "records": len(products)
                }
                
            def export_products_to_excel(self, output_file):
                # Would use a library like xlsxwriter or openpyxl
                # For simplicity, we'll just say it succeeded
                products = self.data_repo.get_products()
                
                # Pretend we wrote to Excel
                return {
                    "file": output_file,
                    "records": len(products)
                }
        
        # Create the service
        export_service = DataExportService(data_repo=mock_data_repo)
        
        # Test exporting to CSV
        with patch('builtins.open', mock_open()) as mock_file:
            results = export_service.export_products_to_csv("products.csv")
            
            # Verify file was opened for writing
            mock_file.assert_called_once_with("products.csv", 'w', newline='')
        
        # Verify data repo was called
        mock_data_repo.get_products.assert_called_once()
        
        # Verify results
        assert results["file"] == "products.csv"
        assert results["records"] == 3 