#!/usr/bin/env python3
"""
Standalone Point API Connector
This demonstrates the core functionality without Airbyte CDK dependencies.
"""

import base64
import csv
import io
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional
import requests


class PointConnector:
    """Standalone Point API connector implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://webservices.verzorgdeoverdracht.nl/api/DistributableData/"
    
    def check_connection(self) -> tuple[bool, Optional[str]]:
        """Test connection to the Point API."""
        try:
            # Validate required configuration
            required_fields = ["api_key", "organization_id"]
            for field in required_fields:
                if field not in self.config:
                    return False, f"Missing required field: {field}"
                if not self.config[field]:
                    return False, f"Field '{field}' cannot be empty"
            
            # Test API connection
            url = f"{self.base_url}GetLatest"
            headers = {
                "APIkey": self.config["api_key"],
                "Accept": "application/json",
                "User-Agent": "Point Connector/1.0"
            }
            params = {
                "OrganizationID": self.config["organization_id"],
                "DistributionTypeID": self.config.get("distribution_type_id", "1")
                # Removed APIkey from query params - using header only
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            self.logger.info(f"API Response Status: {response.status_code}")
            self.logger.info(f"API Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.logger.info(f"API Response JSON keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                    
                    if "Data" in data:
                        self.logger.info("Successfully connected to Point API")
                        return True, None
                    else:
                        return False, f"Invalid response structure from API. Expected 'Data' field. Got: {list(data.keys()) if isinstance(data, dict) else type(data)}"
                except Exception as e:
                    return False, f"Failed to parse JSON response: {str(e)}. Raw response: {response.text[:500]}"
            else:
                return False, f"API returned status {response.status_code}: {response.text}"
                
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def get_specification(self) -> Dict[str, Any]:
        """Return the connector specification."""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Point Source Spec",
            "type": "object",
            "required": ["api_key", "organization_id"],
            "properties": {
                "api_key": {
                    "type": "string",
                    "title": "API Key",
                    "description": "Your Point API key for authentication",
                    "airbyte_secret": True
                },
                "organization_id": {
                    "type": "string",
                    "title": "Organization ID",
                    "description": "Your organization identifier"
                },
                "distribution_type_id": {
                    "type": "string",
                    "title": "Distribution Type ID",
                    "description": "Distribution type identifier (defaults to '1')",
                    "default": "1"
                }
            }
        }
    
    def discover_streams(self) -> Dict[str, Any]:
        """Discover available streams."""
        return {
            "streams": [
                {
                    "name": "point_data",
                    "json_schema": {
                        "$schema": "http://json-schema.org/draft-07/schema#",
                        "type": "object",
                        "properties": {
                            "row_index": {
                                "type": "integer",
                                "description": "Index of the row in the CSV data"
                            },
                            "metadata": {
                                "type": "object",
                                "properties": {
                                    "identifier": {"type": ["string", "null"]},
                                    "file_name": {"type": ["string", "null"]},
                                    "content_type": {"type": ["string", "null"]},
                                    "timestamp": {"type": ["string", "null"], "format": "date-time"},
                                    "api_status": {"type": ["integer", "null"]}
                                }
                            },
                            "data": {
                                "type": "object",
                                "additionalProperties": {"type": ["string", "null"]}
                            }
                        }
                    },
                    "supported_sync_modes": ["full_refresh"]
                }
            ]
        }
    
    def read_records(self, stream_name: str = "point_data") -> List[Dict[str, Any]]:
        """Read records from the Point API."""
        try:
            # Make API request
            url = f"{self.base_url}GetLatest"
            headers = {
                "APIkey": self.config["api_key"],
                "Accept": "application/json",
                "User-Agent": "Point Connector/1.0"
            }
            params = {
                "OrganizationID": self.config["organization_id"],
                "DistributionTypeID": self.config.get("distribution_type_id", "1")
                # Removed APIkey from query params - using header only
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            self.logger.info(f"Read Records - API Response Status: {response.status_code}")
            self.logger.info(f"Read Records - API Response Headers: {dict(response.headers)}")
            
            json_response = response.json()
            self.logger.info(f"Read Records - API Response JSON keys: {list(json_response.keys()) if isinstance(json_response, dict) else type(json_response)}")
            
            # Extract metadata from the response (direct structure, no 'body' wrapper)
            metadata = {
                "identifier": json_response.get("Identifier"),
                "file_name": json_response.get("FileName"),
                "content_type": json_response.get("ContentType"),
                "timestamp": json_response.get("Timestamp"),
                "api_status": response.status_code
            }
            
            # Decode base64 data
            if "Data" not in json_response:
                self.logger.error(f"No 'Data' field in API response. Available fields: {list(json_response.keys()) if isinstance(json_response, dict) else type(json_response)}")
                return []
                
            try:
                # Decode base64 data with proper encoding handling
                csv_bytes = base64.b64decode(json_response["Data"])
                
                # Try different encodings commonly used for CSV files
                encodings = ['utf-8', 'windows-1252', 'iso-8859-1', 'cp1252']
                csv_data = None
                
                for encoding in encodings:
                    try:
                        csv_data = csv_bytes.decode(encoding)
                        self.logger.info(f"Successfully decoded base64 data using {encoding}, length: {len(csv_data)}")
                        break
                    except UnicodeDecodeError:
                        continue
                
                if csv_data is None:
                    self.logger.error("Could not decode CSV data with any supported encoding")
                    return []
                    
            except Exception as e:
                self.logger.error(f"Failed to decode base64 data: {str(e)}")
                return []
            
            # Parse CSV data
            records = []
            
            # Handle CSV with potential sep= header
            csv_lines = csv_data.strip().split('\n')
            if csv_lines and csv_lines[0].startswith('sep='):
                # Skip the sep= line
                csv_content = '\n'.join(csv_lines[1:])
            else:
                csv_content = csv_data
            
            csv_reader = csv.DictReader(io.StringIO(csv_content), delimiter=';')
            
            for row_index, row in enumerate(csv_reader):
                # Clean up the row data - remove empty keys and null values
                cleaned_row = {}
                for key, value in row.items():
                    if key and key.strip() and value is not None:
                        cleaned_row[key.strip()] = value.strip() if isinstance(value, str) else value
                
                record = {
                    "row_index": row_index,
                    "metadata": metadata,
                    "data": cleaned_row
                }
                records.append(record)
            
            self.logger.info(f"Successfully read {len(records)} records")
            return records
            
        except Exception as e:
            self.logger.error(f"Error reading records: {str(e)}")
            raise


def main():
    """Main entry point for the standalone connector."""
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: python standalone_connector.py <command> [--config config.json]")
        print("Commands: spec, check, discover, read")
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Load configuration
    config = {}
    if "--config" in sys.argv:
        config_index = sys.argv.index("--config")
        if config_index + 1 < len(sys.argv):
            config_file = sys.argv[config_index + 1]
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                sys.exit(1)
    
    # Handle commands
    if command == "spec":
        connector = PointConnector({})
        spec = connector.get_specification()
        print(json.dumps(spec, indent=2))
    
    elif command == "check":
        if not config:
            print("Error: --config required for check command")
            sys.exit(1)
        
        connector = PointConnector(config)
        success, error = connector.check_connection()
        
        result = {
            "type": "CONNECTION_STATUS",
            "connectionStatus": {
                "status": "SUCCEEDED" if success else "FAILED",
                "message": error if error else "Connection successful"
            }
        }
        print(json.dumps(result, indent=2))
    
    elif command == "discover":
        if not config:
            print("Error: --config required for discover command")
            sys.exit(1)
        
        connector = PointConnector(config)
        catalog = connector.discover_streams()
        
        result = {
            "type": "CATALOG",
            "catalog": catalog
        }
        print(json.dumps(result, indent=2))
    
    elif command == "read":
        if not config:
            print("Error: --config required for read command")
            sys.exit(1)
        
        connector = PointConnector(config)
        records = connector.read_records()
        
        for record in records[:5]:  # Limit to first 5 records for demo
            result = {
                "type": "RECORD",
                "record": {
                    "stream": "point_data",
                    "data": record,
                    "emitted_at": 1640995200000  # Example timestamp
                }
            }
            print(json.dumps(result, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()