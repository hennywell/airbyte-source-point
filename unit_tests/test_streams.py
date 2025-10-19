#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#

import base64
import json
from unittest.mock import Mock, patch
import pytest
import requests
from source_point.streams import PointStream


class TestPointStream:
    """Test cases for PointStream class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "api_key": "test_api_key",
            "organization_id": "test_org_id",
            "distribution_type_id": "1"
        }
        self.stream = PointStream(config=self.config)

    def test_stream_name(self):
        """Test that stream has correct name."""
        assert self.stream.name == "point_data"

    def test_path(self):
        """Test that path returns correct endpoint."""
        assert self.stream.path() == "GetLatest"

    def test_request_headers(self):
        """Test request headers are correctly formatted."""
        headers = self.stream.request_headers()
        
        assert "APIkey" in headers
        assert headers["APIkey"] == "test_api_key"
        assert headers["Accept"] == "application/json"
        assert "User-Agent" in headers

    def test_request_params(self):
        """Test request parameters are correctly formatted."""
        params = self.stream.request_params()
        
        assert params["OrganizationID"] == "test_org_id"
        assert params["DistributionTypeID"] == "1"
        # APIkey is now in headers only, not in params
        assert "APIkey" not in params

    def test_request_params_default_distribution_type(self):
        """Test default distribution type ID."""
        config_without_dist_type = {
            "api_key": "test_api_key",
            "organization_id": "test_org_id"
        }
        stream = PointStream(config=config_without_dist_type)
        params = stream.request_params()
        
        assert params["DistributionTypeID"] == "1"

    def test_get_json_schema(self):
        """Test that JSON schema is properly defined."""
        schema = self.stream.get_json_schema()
        
        assert schema["type"] == "object"
        assert "properties" in schema
        
        properties = schema["properties"]
        assert "_metadata_identifier" in properties  # Metadata field
        assert "_metadata_timestamp" in properties   # Metadata field
        assert "_metadata_file_name" in properties   # Metadata field
        assert "TransferID" in properties           # Primary key field
        assert "TransferCreatedDate" in properties  # Cursor field
        # Check that primary key is properly defined
        assert properties["TransferID"]["description"] == "CSV column: TransferID (Primary Key)"
        assert properties["TransferCreatedDate"]["description"] == "CSV column: TransferCreatedDate (Cursor Field)"
        assert "metadata" not in properties
        assert "data" not in properties

    def test_parse_response_success(self):
        """Test successful response parsing."""
        # Create test CSV data
        csv_data = "column1;column2;column3\nvalue1;value2;value3\nvalue4;value5;value6"
        encoded_data = base64.b64encode(csv_data.encode('utf-8')).decode('utf-8')
        
        # Mock API response - updated to match actual API structure
        mock_response_data = {
            "Identifier": "test-id-123",
            "FileName": "test.csv",
            "ContentType": "text/csv",
            "Timestamp": "2023-01-01T12:00:00Z",
            "Data": encoded_data
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        
        # Parse response
        records = list(self.stream.parse_response(mock_response))
        
        # Verify results
        assert len(records) == 2  # Two data rows
        
        # Check first record - flattened structure
        first_record = records[0]
        assert first_record["_metadata_identifier"] == "test-id-123"  # Metadata
        assert first_record["_metadata_file_name"] == "test.csv"     # Metadata
        assert first_record["_metadata_timestamp"] == "2023-01-01T12:00:00Z"  # Metadata
        assert first_record["column1"] == "value1"         # CSV data flattened
        assert first_record["column2"] == "value2"         # CSV data flattened
        assert first_record["column3"] == "value3"         # CSV data flattened
        
        # Check second record
        second_record = records[1]
        assert second_record["_metadata_identifier"] == "test-id-123"  # Same metadata
        assert second_record["column1"] == "value4"        # CSV data flattened
        assert second_record["column2"] == "value5"        # CSV data flattened
        assert second_record["column3"] == "value6"        # CSV data flattened

    def test_parse_response_missing_body(self):
        """Test response parsing with missing body."""
        mock_response_data = {}  # Empty response
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        
        records = list(self.stream.parse_response(mock_response))
        assert len(records) == 0

    def test_parse_response_missing_data(self):
        """Test response parsing with missing Data field."""
        mock_response_data = {
            "Identifier": "test-id-123",
            "FileName": "test.csv"
            # Missing "Data" field
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        
        records = list(self.stream.parse_response(mock_response))
        assert len(records) == 0

    def test_parse_response_invalid_base64(self):
        """Test response parsing with invalid base64 data."""
        mock_response_data = {
            "Identifier": "test-id-123",
            "FileName": "test.csv",
            "ContentType": "text/csv",
            "Timestamp": "2023-01-01T12:00:00Z",
            "Data": "invalid_base64_data!!!"
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        
        records = list(self.stream.parse_response(mock_response))
        assert len(records) == 0

    @patch('requests.get')
    def test_test_connection_success(self, mock_get):
        """Test successful connection test."""
        # Mock successful response
        csv_data = "col1;col2\nval1;val2"
        encoded_data = base64.b64encode(csv_data.encode('utf-8')).decode('utf-8')
        
        mock_response_data = {
            "Identifier": "test-id",
            "FileName": "test.csv",
            "Data": encoded_data
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_get.return_value = mock_response
        
        result = self.stream.test_connection()
        assert result is True

    @patch('requests.get')
    def test_test_connection_failure(self, mock_get):
        """Test failed connection test."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response
        
        result = self.stream.test_connection()
        assert result is False

    @patch('requests.get')
    def test_test_connection_exception(self, mock_get):
        """Test connection test with exception."""
        mock_get.side_effect = requests.RequestException("Network error")
        
        result = self.stream.test_connection()
        assert result is False