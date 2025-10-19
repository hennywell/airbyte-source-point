#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#

import pytest
from unittest.mock import Mock, patch
from source_point.source import SourcePoint


class TestSourcePoint:
    """Test cases for SourcePoint class."""

    def test_spec(self):
        """Test that spec returns the correct specification."""
        source = SourcePoint()
        logger = Mock()
        spec = source.spec(logger)
        
        assert spec.connectionSpecification is not None
        assert "properties" in spec.connectionSpecification
        
        properties = spec.connectionSpecification["properties"]
        assert "api_key" in properties
        assert "organization_id" in properties
        assert "distribution_type_id" in properties
        
        # Check required fields
        required = spec.connectionSpecification["required"]
        assert "api_key" in required
        assert "organization_id" in required

    def test_check_connection_missing_config(self):
        """Test connection check with missing configuration."""
        source = SourcePoint()
        logger = Mock()
        
        # Test missing api_key
        config = {"organization_id": "123"}
        success, error = source.check_connection(logger, config)
        assert not success
        assert "api_key" in error
        
        # Test missing organization_id
        config = {"api_key": "test_key"}
        success, error = source.check_connection(logger, config)
        assert not success
        assert "organization_id" in error

    def test_check_connection_empty_config(self):
        """Test connection check with empty configuration values."""
        source = SourcePoint()
        logger = Mock()
        
        # Test empty api_key
        config = {"api_key": "", "organization_id": "123"}
        success, error = source.check_connection(logger, config)
        assert not success
        assert "api_key" in error

    @patch('source_point.streams.PointStream.test_connection')
    def test_check_connection_success(self, mock_test_connection):
        """Test successful connection check."""
        mock_test_connection.return_value = True
        
        source = SourcePoint()
        logger = Mock()
        config = {"api_key": "test_key", "organization_id": "123"}
        
        success, error = source.check_connection(logger, config)
        assert success
        assert error is None

    @patch('source_point.streams.PointStream.test_connection')
    def test_check_connection_failure(self, mock_test_connection):
        """Test failed connection check."""
        mock_test_connection.return_value = False
        
        source = SourcePoint()
        logger = Mock()
        config = {"api_key": "test_key", "organization_id": "123"}
        
        success, error = source.check_connection(logger, config)
        assert not success
        assert "Failed to connect" in error

    def test_streams(self):
        """Test that streams returns the correct stream instances."""
        source = SourcePoint()
        config = {"api_key": "test_key", "organization_id": "123"}
        
        streams = source.streams(config)
        assert len(streams) == 1
        assert streams[0].name == "point_data"