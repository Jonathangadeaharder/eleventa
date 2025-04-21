import sqlite3

class Database:
    """
    A simple SQLite database wrapper for direct SQL operations.
    This class provides basic database operations for direct SQL execution.
    """
    
    def __init__(self, db_path):
        """
        Initialize a database connection.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.connection = sqlite3.connect(db_path)
        self.in_transaction = False
    
    def execute_query(self, query, params=()):
        """
        Execute a SQL query with parameters.
        
        Args:
            query (str): SQL query to execute
            params (tuple): Parameters for the query
            
        Returns:
            None
        """
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()
        
    def execute_query_with_return(self, query, params=()):
        """
        Execute a SQL query and return the results.
        
        Args:
            query (str): SQL query to execute
            params (tuple): Parameters for the query
            
        Returns:
            list: Results of the query
        """
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def execute_many(self, query, params_list):
        """
        Execute a SQL query multiple times with different parameters.
        
        Args:
            query (str): SQL query to execute
            params_list (list): List of parameter tuples
            
        Returns:
            None
        """
        cursor = self.connection.cursor()
        cursor.executemany(query, params_list)
        self.connection.commit()
    
    def get_last_row_id(self):
        """
        Get the ID of the last inserted row.
        
        Returns:
            int: Last row ID
        """
        cursor = self.connection.cursor()
        return cursor.lastrowid
    
    def close_connection(self):
        """
        Close the database connection.
        """
        self.connection.close()
    
    def begin_transaction(self):
        """
        Begin a database transaction.
        """
        self.in_transaction = True
    
    def commit_transaction(self):
        """
        Commit the current transaction.
        """
        self.connection.commit()
        self.in_transaction = False
    
    def rollback_transaction(self):
        """
        Rollback the current transaction.
        """
        self.connection.rollback()
        self.in_transaction = False 