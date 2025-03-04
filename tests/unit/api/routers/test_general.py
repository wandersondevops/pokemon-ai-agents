"""
Tests for the general router.

This module contains tests for the general router endpoints.
"""

import pytest
from unittest.mock import patch, mock_open, MagicMock
from fastapi.testclient import TestClient
from fastapi import status
from pathlib import Path

from app.main import app

class TestGeneralRouter:
    """Tests for the general router."""
    
    @patch('app.api.routers.general.Path')
    @patch('app.api.routers.general.open', new_callable=mock_open, read_data="<html>Test HTML</html>")
    def test_root_endpoint_existing_file(self, mock_file, mock_path, test_client):
        """Test the root endpoint when index.html exists."""
        # Setup mock path
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value.parent.parent.parent.parent.__truediv__.return_value = mock_path_instance
        mock_path_instance.__truediv__.return_value = mock_path_instance
        
        # Make request
        response = test_client.get("/")
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        assert response.text == "<html>Test HTML</html>"
        
        # Verify mock was called correctly
        mock_path_instance.exists.assert_called_once()
        mock_file.assert_called_once()
    
    @patch('app.api.routers.general.Path')
    @patch('app.api.routers.general.os.makedirs')
    @patch('app.api.routers.general.open', new_callable=mock_open)
    def test_root_endpoint_create_file(self, mock_file, mock_makedirs, mock_path, test_client):
        """Test the root endpoint when index.html doesn't exist."""
        # Setup mock path
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = False
        mock_path.return_value.parent.parent.parent.parent.__truediv__.return_value = mock_path_instance
        mock_path_instance.__truediv__.return_value = mock_path_instance
        
        # Setup mock file to return different content when read
        mock_file.return_value.__enter__.return_value.read.return_value = "<!DOCTYPE html>"
        
        # Make request
        response = test_client.get("/")
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        assert "<!DOCTYPE html>" in response.text
        
        # Verify mocks were called correctly
        mock_path_instance.exists.assert_called_once()
        mock_makedirs.assert_called_once()
        assert mock_file.call_count == 2  # Once for writing, once for reading
        
        # Verify the file was written with HTML content
        write_call = mock_file.return_value.__enter__.return_value.write.call_args[0][0]
        assert "<!DOCTYPE html>" in write_call
        assert "Pokemon AI Agents API" in write_call
    
    @patch('app.api.routers.general.Path')
    def test_root_endpoint_error(self, mock_path, test_client):
        """Test the root endpoint when an error occurs."""
        # Setup mock path to raise an exception
        mock_path.side_effect = Exception("Test error")
        
        # Make request
        response = test_client.get("/")
        
        # Assertions
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        response_data = response.json()
        assert "detail" in response_data
        assert "An error occurred" in response_data["detail"]
