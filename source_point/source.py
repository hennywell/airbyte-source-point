#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#

import logging
from typing import Any, List, Mapping, Optional, Tuple

from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.models import ConnectorSpecification

from .streams import PointStream


class SourcePoint(AbstractSource):
    """
    Source implementation for Point API.
    
    This connector fetches data from the Point API which returns base64-encoded CSV data
    and transforms it into structured records for Airbyte.
    """

    def check_connection(self, logger: logging.Logger, config: Mapping[str, Any]) -> Tuple[bool, Optional[Any]]:
        """
        Verify that the connector can connect to the Point API with the provided configuration.
        
        Args:
            logger: Airbyte logger
            config: Configuration dictionary containing API credentials
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            # Validate required configuration fields
            required_fields = ["api_key", "organization_id"]
            for field in required_fields:
                if field not in config:
                    return False, f"Missing required configuration field: {field}"
                if not config[field]:
                    return False, f"Configuration field '{field}' cannot be empty"

            # Test API connection by creating a stream and making a test request
            stream = PointStream(config=config)
            test_response = stream.test_connection()
            
            if test_response:
                logger.info("Successfully connected to Point API")
                return True, None
            else:
                return False, "Failed to connect to Point API"
                
        except Exception as e:
            logger.error(f"Connection check failed: {str(e)}")
            return False, f"Connection failed: {str(e)}"

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        """
        Return the list of streams supported by this connector.
        
        Args:
            config: Configuration dictionary containing API credentials
            
        Returns:
            List of Stream instances
        """
        return [PointStream(config=config)]

    def spec(self, logger: logging.Logger) -> ConnectorSpecification:
        """
        Define the connector specification including configuration schema.
        
        Args:
            logger: Logger instance
            
        Returns:
            ConnectorSpecification with configuration schema
        """
        return ConnectorSpecification(
            connectionSpecification={
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Point Source Spec",
                "type": "object",
                "required": ["api_key", "organization_id"],
                "additionalProperties": True,
                "properties": {
                    "api_key": {
                        "type": "string",
                        "title": "API Key",
                        "description": "Your Point API key for authentication",
                        "airbyte_secret": True,
                        "order": 0
                    },
                    "organization_id": {
                        "type": "string",
                        "title": "Organization ID",
                        "description": "Your organization identifier",
                        "examples": ["12345"],
                        "order": 1
                    },
                    "distribution_type_id": {
                        "type": "string",
                        "title": "Distribution Type ID",
                        "description": "Distribution type identifier (defaults to '1')",
                        "default": "1",
                        "examples": ["1", "2", "3"],
                        "order": 2
                    }
                }
            }
        )