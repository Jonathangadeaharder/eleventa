"""
Mock utilities for external services and dependencies.

This module provides fixtures and utilities for mocking external services
like HTTP APIs, file systems, and other external dependencies to improve
test isolation.
"""
import pytest
from unittest.mock import MagicMock, patch
import requests
import os
import tempfile

# Store original os.path functions before patching
original_os_path_exists = os.path.exists
original_os_path_isfile = os.path.isfile
original_os_listdir = os.listdir
original_open = open


class MockResponse:
    """Mock HTTP response object that mimics requests.Response."""
    
    def __init__(self, status_code=200, json_data=None, text="", headers=None):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text
        self.headers = headers or {}
        self.content = text.encode() if isinstance(text, str) else text
        
    def json(self):
        return self._json_data
        
    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"Mock HTTP Error: {self.status_code}")


@pytest.fixture
def mock_http_client():
    """
    Fixture that provides a mock HTTP client for integration tests.
    
    Returns a MagicMock configured to return controllable MockResponse objects.
    
    Example usage:
    ```
    def test_api_call(mock_http_client):
        # Configure mock response
        mock_http_client.get.return_value = MockResponse(
            status_code=200,
            json_data={"result": "success"}
        )
        
        # Test code that uses requests.get
        result = my_service.fetch_data_from_api()
        assert result == "success"
    ```
    """
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post, \
         patch('requests.put') as mock_put, \
         patch('requests.delete') as mock_delete:
        
        # Create callable mocks for each HTTP method
        client = MagicMock()
        client.get = mock_get
        client.post = mock_post
        client.put = mock_put
        client.delete = mock_delete
        
        # Configure default return values
        default_response = MockResponse(200, {})
        mock_get.return_value = default_response
        mock_post.return_value = default_response
        mock_put.return_value = default_response
        mock_delete.return_value = default_response
        
        yield client


@pytest.fixture
def mock_file_system():
    """
    Fixture that provides a mock file system for integration tests.
    
    Creates a temporary directory for file operations and patches
    os.path functions to use this directory.
    
    Example usage:
    ```
    def test_file_operations(mock_file_system):
        # Test code that reads/writes files
        my_service.write_log_file("log.txt", "Test log entry")
        
        # Check that file was created in the temp directory
        assert mock_file_system.file_exists("log.txt")
        assert mock_file_system.read_file("log.txt") == "Test log entry"
    ```
    """
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a helper class to manage the mock file system
        class MockFileSystem:
            def __init__(self, base_dir):
                self.base_dir = base_dir
                # Store internal file representations (path -> content)
                self._files = {}
                
            def get_path(self, relative_path):
                # Ensure paths are normalized for the OS
                normalized_path = os.path.normpath(relative_path)
                # Prevent accessing files outside the base_dir (security measure)
                full_path = os.path.abspath(os.path.join(self.base_dir, normalized_path))
                if not full_path.startswith(os.path.abspath(self.base_dir)):
                    raise ValueError("Attempted to access path outside the mock filesystem base directory")
                return full_path
                
            def file_exists(self, relative_path):
                # Use the original os.path.exists on the actual temp path
                actual_path = self.get_path(relative_path)
                return original_os_path_exists(actual_path) 
                
            def read_file(self, relative_path):
                actual_path = self.get_path(relative_path)
                # Use original open to interact with the real temp file
                with original_open(actual_path, 'r') as f:
                    return f.read()
                    
            def write_file(self, relative_path, content):
                actual_path = self.get_path(relative_path)
                # Ensure directory exists
                os.makedirs(os.path.dirname(actual_path), exist_ok=True)
                # Use original open to interact with the real temp file
                with original_open(actual_path, 'w') as f:
                    f.write(content)
                    
            def list_files(self):
                # Use the original os.listdir
                return original_os_listdir(self.base_dir)
        
        # Create the mock file system
        fs = MockFileSystem(temp_dir)
        
        # --- Patching Strategy ---
        # Instead of patching os.path.exists globally, we rely on the 
        # test_app fixture providing this 'fs' object. 
        # Code under test should be modified/injected to use fs.file_exists, 
        # fs.read_file etc., instead of direct os calls when under test.
        # However, if patching is absolutely necessary for legacy code or 
        # libraries you don't control, the previous patch approach had a 
        # recursion error. A corrected patch would look like:
        # 
        # def patched_exists(path):
        #     # Check if the path is within our mocked directory
        #     abs_path = os.path.abspath(path)
        #     abs_base_dir = os.path.abspath(fs.base_dir)
        #     if abs_path.startswith(abs_base_dir):
        #         relative_path = os.path.relpath(abs_path, abs_base_dir)
        #         return fs.file_exists(relative_path) # Calls original_os_path_exists internally
        #     else:
        #         # If path is outside mock dir, call original function
        #         return original_os_path_exists(path)
        # 
        # with patch('os.path.exists', side_effect=patched_exists), \
        #      patch('os.path.isfile', side_effect=patched_exists): # isfile often relies on exists
        #     yield fs 
        # 
        # For now, we remove the global patches as they caused recursion and 
        # assume injection of the mock filesystem object is the preferred pattern.
        
        yield fs # Yield the mock fs object without global patches


@pytest.fixture
def mock_external_services(mock_http_client, mock_file_system):
    """
    Composite fixture that combines all external service mocks.
    
    This fixture provides a comprehensive set of mocks for all
    external dependencies, making it easy to isolate tests from
    external systems.
    
    Returns:
        dict: A dictionary containing all mock services.
    """
    return {
        "http": mock_http_client,
        "filesystem": mock_file_system
    } 