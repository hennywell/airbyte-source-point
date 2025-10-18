#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#

import os
import pytest
from source_point.source import SourcePoint


class TestIntegration:
    """Integration tests for Point connector."""

    @pytest.fixture
    def config(self):
        """Load configuration from environment variables."""
        return {
            "api_key": os.getenv("POINT_API_KEY"),
            "organization_id": os.getenv("POINT_ORGANIZATION_ID"),
            "distribution_type_id": os.getenv("POINT_DISTRIBUTION_TYPE_ID", "1")
        }

    @pytest.mark.skipif(
        not os.getenv("POINT_API_KEY") or not os.getenv("POINT_ORGANIZATION_ID"),
        reason="Integration test requires POINT_API_KEY and POINT_ORGANIZATION_ID environment variables"
    )
    def test_check_connection_integration(self, config):
        """Test connection check with real API credentials."""
        source = SourcePoint()
        
        # Mock logger
        class MockLogger:
            def info(self, msg): pass
            def error(self, msg): pass
        
        logger = MockLogger()
        success, error = source.check_connection(logger, config)
        
        assert success, f"Connection check failed: {error}"

    @pytest.mark.skipif(
        not os.getenv("POINT_API_KEY") or not os.getenv("POINT_ORGANIZATION_ID"),
        reason="Integration test requires POINT_API_KEY and POINT_ORGANIZATION_ID environment variables"
    )
    def test_discover_integration(self, config):
        """Test stream discovery with real API credentials."""
        source = SourcePoint()
        streams = source.streams(config)
        
        assert len(streams) == 1
        assert streams[0].name == "point_data"

    @pytest.mark.skipif(
        not os.getenv("POINT_API_KEY") or not os.getenv("POINT_ORGANIZATION_ID"),
        reason="Integration test requires POINT_API_KEY and POINT_ORGANIZATION_ID environment variables"
    )
    def test_read_records_integration(self, config):
        """Test reading records from real API."""
        source = SourcePoint()
        streams = source.streams(config)
        stream = streams[0]
        
        # Read a few records to test the integration
        records = []
        for record in stream.read_records(sync_mode="full_refresh"):
            records.append(record)
            # Limit to first 10 records for testing
            if len(records) >= 10:
                break
        
        # Verify we got some records
        assert len(records) > 0, "No records were returned from the API"
        
        # Verify record structure
        first_record = records[0]
        assert "row_index" in first_record
        assert "metadata" in first_record
        assert "data" in first_record
        
        # Verify metadata structure
        metadata = first_record["metadata"]
        assert "identifier" in metadata
        assert "file_name" in metadata
        assert "timestamp" in metadata
        
        # Verify data is a dictionary
        assert isinstance(first_record["data"], dict)