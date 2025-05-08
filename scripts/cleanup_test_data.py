#!/usr/bin/env python
"""
Cleanup script for removing test data from production database.
This script should be run on your production database to remove any test data
that might have accidentally been created during testing.
"""
import sys
import os
import argparse
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker

def confirm_action(prompt):
    """Ask for confirmation before executing a potentially destructive action."""
    confirmation = input(f"{prompt} [y/N]: ").lower()
    return confirmation == 'y'

def cleanup_test_data(db_url, dry_run=True):
    """
    Clean up test data from the database.
    
    Args:
        db_url: Database connection URL
        dry_run: If True, will only print what would be deleted without actually deleting
    """
    print(f"{'DRY RUN - ' if dry_run else ''}Connecting to database: {db_url}")
    
    # Create engine and session
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Find test suppliers that match the patterns used in tests
        test_supplier_query = text("SELECT id, name, cuit FROM suppliers WHERE name LIKE 'TEST\\_%' OR name LIKE 'Test Supplier%'")
        test_suppliers = session.execute(test_supplier_query).fetchall()
        
        if not test_suppliers:
            print("No test suppliers found.")
        else:
            print(f"Found {len(test_suppliers)} test suppliers:")
            for supplier in test_suppliers:
                print(f"  ID: {supplier.id}, Name: {supplier.name}, CUIT: {supplier.cuit}")
            
            if not dry_run:
                # Delete test suppliers
                delete_suppliers_query = text("DELETE FROM suppliers WHERE name LIKE 'TEST\\_%' OR name LIKE 'Test Supplier%'")
                result = session.execute(delete_suppliers_query)
                session.commit()
                print(f"Deleted {result.rowcount} test suppliers.")
            else:
                print("DRY RUN - No changes made.")
        
        # Find any POs that might be without suppliers due to test data cleanup
        orphaned_po_query = text("""
            SELECT id, supplier_id FROM purchase_orders 
            WHERE supplier_id NOT IN (SELECT id FROM suppliers)
        """)
        orphaned_pos = session.execute(orphaned_po_query).fetchall()
        
        if orphaned_pos:
            print(f"Found {len(orphaned_pos)} orphaned purchase orders:")
            for po in orphaned_pos:
                print(f"  PO ID: {po.id}, Missing Supplier ID: {po.supplier_id}")
            
            if not dry_run:
                # Delete orphaned PO items first
                delete_orphaned_items_query = text("""
                    DELETE FROM purchase_order_items 
                    WHERE order_id IN (
                        SELECT id FROM purchase_orders 
                        WHERE supplier_id NOT IN (SELECT id FROM suppliers)
                    )
                """)
                items_result = session.execute(delete_orphaned_items_query)
                
                # Then delete orphaned POs
                delete_orphaned_po_query = text("""
                    DELETE FROM purchase_orders 
                    WHERE supplier_id NOT IN (SELECT id FROM suppliers)
                """)
                po_result = session.execute(delete_orphaned_po_query)
                
                session.commit()
                print(f"Deleted {items_result.rowcount} orphaned PO items and {po_result.rowcount} orphaned POs.")
            else:
                print("DRY RUN - No changes made.")
        else:
            print("No orphaned purchase orders found.")
            
    except Exception as e:
        print(f"Error during cleanup: {e}")
        session.rollback()
    finally:
        session.close()

def get_database_url():
    """Get database URL from environment or configuration."""
    # Try to get from environment variable
    db_url = os.environ.get('DATABASE_URL')
    
    # If not in environment, try to read from app_config.json
    if not db_url:
        try:
            import json
            config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app_config.json'))
            print(f"Looking for configuration at {config_path}")
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                print("Configuration loaded from", config_path)
                
                # Extract database configuration from the app_config structure
                if 'database' in config:
                    db_config = config['database']
                    if 'connection_string' in db_config:
                        db_url = db_config['connection_string']
                    elif 'type' in db_config and db_config['type'] == 'sqlite':
                        db_path = db_config.get('path', 'eleventa.db')
                        db_url = f"sqlite:///{db_path}"
            else:
                print(f"Configuration file not found at {config_path}")
                
        except Exception as e:
            print(f"Error reading configuration: {e}")
            
    return db_url

def main():
    """Main function to parse arguments and run the cleanup."""
    parser = argparse.ArgumentParser(description='Clean up test data from production database')
    parser.add_argument('--db-url', help='Database connection URL')
    parser.add_argument('--force', action='store_true', help='Execute deletion without confirmation')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without actually deleting')
    
    args = parser.parse_args()
    
    # Get database URL from arguments or environment
    db_url = args.db_url or get_database_url()
    
    # If no URL detected, use default from file that we found
    if not db_url:
        # Use the database file found in the project directory
        db_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'eleventa_clone.db'))
        if os.path.exists(db_file):
            db_url = f"sqlite:///{db_file}"
            print(f"Using database file: {db_file}")
        else:
            print(f"Error: Default database file not found at {db_file}")
            sys.exit(1)
    
    # Always do a dry run first
    print("Performing dry run to identify test data...")
    cleanup_test_data(db_url, dry_run=True)
    
    # Ask for confirmation before actual deletion
    if not args.dry_run:
        if args.force or confirm_action("Proceed with deletion of test data?"):
            print("\nExecuting actual cleanup...")
            cleanup_test_data(db_url, dry_run=False)
        else:
            print("Cleanup cancelled.")

if __name__ == "__main__":
    main() 