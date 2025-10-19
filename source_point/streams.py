#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#

import base64
import csv
import io
import json
import logging
import os
from typing import Any, Iterable, List, Mapping, Optional

import requests
from airbyte_cdk.sources.streams.http import HttpStream


class PointStream(HttpStream):
    """
    Stream implementation for Point API.
    
    This stream fetches data from the Point API, which returns base64-encoded CSV data,
    and transforms it into structured records with flattened schema.
    """

    url_base = "https://webservices.verzorgdeoverdracht.nl/api/DistributableData/"
    primary_key = "TransferID"  # Use TransferID as primary key
    cursor_field = "TransferCreatedDate"  # Use TransferCreatedDate as cursor field
    http_method = "GET"

    def __init__(self, config: Mapping[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.api_key = config["api_key"]
        self.organization_id = config["organization_id"]
        self.distribution_type_id = config.get("distribution_type_id", "1")

    @property
    def name(self) -> str:
        """Stream name"""
        return "point_data"

    def path(
        self,
        stream_state: Optional[Mapping[str, Any]] = None,
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> str:
        """
        Return the API endpoint path.
        """
        return "GetLatest"

    def request_headers(
        self,
        stream_state: Optional[Mapping[str, Any]] = None,
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> Mapping[str, str]:
        """
        Return headers for the API request.
        """
        return {
            "APIkey": self.api_key,
            "Accept": "application/json",
            "User-Agent": "Airbyte Point Connector/1.0"
        }

    def request_params(
        self,
        stream_state: Optional[Mapping[str, Any]] = None,
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> Mapping[str, Any]:
        """
        Return query parameters for the API request.
        """
        return {
            "OrganizationID": self.organization_id,
            "DistributionTypeID": self.distribution_type_id
            # Removed APIkey from query params - using header only for better security
        }

    def next_page_token(
        self,
        response: requests.Response,
        stream_state: Optional[Mapping[str, Any]] = None,
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> Optional[Mapping[str, Any]]:
        """
        Return the next page token for pagination.
        
        Since the Point API returns all data in a single response,
        there is no pagination, so we always return None.
        """
        return None

    def request_body_json(
        self,
        stream_state: Optional[Mapping[str, Any]] = None,
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> Optional[Mapping[str, Any]]:
        """
        Return the request body for POST requests.
        Since we use GET requests, this returns None.
        """
        return None

    def should_retry(self, response: requests.Response) -> bool:
        """
        Override to define custom retry logic.
        """
        return response.status_code >= 500 or response.status_code == 429

    def backoff_time(self, response: requests.Response) -> Optional[float]:
        """
        Override to define custom backoff time.
        """
        if response.status_code == 429:
            # Rate limited - wait 60 seconds
            return 60.0
        elif response.status_code >= 500:
            # Server error - wait 30 seconds
            return 30.0
        return None

    def parse_response(
        self,
        response: requests.Response,
        stream_state: Optional[Mapping[str, Any]] = None,
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> Iterable[Mapping[str, Any]]:
        """
        Parse the API response and yield records.
        
        The API returns a JSON response with base64-encoded CSV data.
        We decode the CSV and yield each row as a record.
        """
        try:
            json_response = response.json()
            
            # Extract metadata from the response (direct structure, no 'body' wrapper)
            metadata = {
                "metainfo_identifier": json_response.get("Identifier"),
                "metainfo_file_name": json_response.get("FileName"),
                "metainfo_timestamp": json_response.get("Timestamp")
            }
            
            # Decode base64 data
            if "Data" not in json_response:
                logging.error(f"No 'Data' field found in API response. Available fields: {list(json_response.keys()) if isinstance(json_response, dict) else type(json_response)}")
                return
                
            try:
                # Decode base64 data with proper encoding handling
                csv_bytes = base64.b64decode(json_response["Data"])
                
                # Try different encodings commonly used for CSV files
                encodings = ['utf-8', 'windows-1252', 'iso-8859-1', 'cp1252']
                csv_data = None
                
                for encoding in encodings:
                    try:
                        csv_data = csv_bytes.decode(encoding)
                        logging.info(f"Successfully decoded base64 data using {encoding}, length: {len(csv_data)}")
                        break
                    except UnicodeDecodeError:
                        continue
                
                if csv_data is None:
                    logging.error("Could not decode CSV data with any supported encoding")
                    return
                    
            except Exception as e:
                logging.error(f"Failed to decode base64 data: {str(e)}")
                return
            
            # Parse CSV data
            # Handle CSV with potential sep= header
            csv_lines = csv_data.strip().split('\n')
            if csv_lines and csv_lines[0].startswith('sep='):
                # Skip the sep= line
                csv_content = '\n'.join(csv_lines[1:])
            else:
                csv_content = csv_data
            
            csv_reader = csv.DictReader(io.StringIO(csv_content), delimiter=';')
            
            # Load schema to identify field types for proper data conversion
            schema = self.get_json_schema()
            schema_properties = schema.get("properties", {})
            
            for row_index, row in enumerate(csv_reader):
                # Clean up the row data with proper type conversion
                cleaned_row = {}
                for key, value in row.items():
                    if key and key.strip():
                        clean_key = key.strip()
                        cleaned_value = self._convert_field_value(clean_key, value, schema_properties)
                        # Always include the field, even if null, to maintain schema consistency
                        cleaned_row[clean_key] = cleaned_value
                
                # Create flattened record with metadata and CSV data at top level
                record = {
                    # Metadata fields at top level
                    "metainfo_identifier": metadata["metainfo_identifier"],
                    "metainfo_timestamp": metadata["metainfo_timestamp"],
                    "metainfo_file_name": metadata["metainfo_file_name"]
                }
                
                # Add all CSV columns at top level
                record.update(cleaned_row)
                
                yield record
                
        except Exception as e:
            logging.error(f"Error parsing response: {str(e)}")
            raise

    def get_json_schema(self) -> Mapping[str, Any]:
        """
        Return the JSON schema for this stream.
        Dynamically discovers CSV columns from the API response.
        """
        schema_path = os.path.join(os.path.dirname(__file__), "schemas", "point_data.json")
        try:
            with open(schema_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            # Try to discover schema dynamically from API
            try:
                discovered_schema = self._discover_schema_from_api()
                if discovered_schema:
                    return discovered_schema
            except Exception as e:
                logging.warning(f"Failed to discover schema from API: {str(e)}")
            
            # Fallback schema if file not found and API discovery fails
            return {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "metainfo_identifier": {
                        "type": ["string", "null"],
                        "description": "Unique identifier from the API response (Primary Key)"
                    },
                    "metainfo_timestamp": {
                        "type": ["string", "null"],
                        "format": "date-time",
                        "description": "Timestamp when the data was generated (Cursor Field)"
                    },
                    "metainfo_file_name": {
                        "type": ["string", "null"],
                        "description": "Name of the CSV file"
                    }
                },
                "additionalProperties": {
                    "type": ["string", "null", "integer", "number", "boolean"],
                    "description": "CSV column data - dynamically added based on CSV structure"
                }
            }

    def _discover_schema_from_api(self) -> Optional[Mapping[str, Any]]:
        """
        Discover schema by making a test API call and analyzing the CSV structure.
        """
        try:
            # Make a test request to the API
            url = f"{self.url_base}{self.path()}"
            headers = self.request_headers()
            params = self.request_params()
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code != 200:
                return None
                
            json_response = response.json()
            if "Data" not in json_response:
                return None
            
            # Decode base64 data
            csv_bytes = base64.b64decode(json_response["Data"])
            
            # Try different encodings
            encodings = ['utf-8', 'windows-1252', 'iso-8859-1', 'cp1252']
            csv_data = None
            
            for encoding in encodings:
                try:
                    csv_data = csv_bytes.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if csv_data is None:
                return None
            
            # Parse CSV to get column names
            csv_lines = csv_data.strip().split('\n')
            if csv_lines and csv_lines[0].startswith('sep='):
                csv_content = '\n'.join(csv_lines[1:])
            else:
                csv_content = csv_data
            
            csv_reader = csv.DictReader(io.StringIO(csv_content), delimiter=';')
            
            # Get the first row to determine column names and types
            first_row = next(csv_reader, None)
            if not first_row:
                return None
            
            # Build schema with discovered columns
            properties = {
                # Metadata fields
                "metainfo_identifier": {
                    "type": ["string", "null"],
                    "description": "Unique identifier from the API response (Primary Key)"
                },
                "metainfo_timestamp": {
                    "type": ["string", "null"],
                    "format": "date-time",
                    "description": "Timestamp when the data was generated (Cursor Field)"
                },
                "metainfo_file_name": {
                    "type": ["string", "null"],
                    "description": "Name of the CSV file"
                }
            }
            
            # Add CSV columns
            for column_name, value in first_row.items():
                if column_name and column_name.strip():
                    clean_name = column_name.strip()
                    # Try to infer type from the value
                    column_type = self._infer_column_type(value)
                    properties[clean_name] = {
                        "type": column_type,
                        "description": f"CSV column: {clean_name}"
                    }
            
            return {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": properties
            }
            
        except Exception as e:
            logging.error(f"Error discovering schema from API: {str(e)}")
            return None

    def _infer_column_type(self, value: str) -> List[str]:
        """
        Infer the JSON schema type from a CSV value.
        """
        if not value or value.strip() == "":
            return ["string", "null"]
        
        value = value.strip()
        
        # Try integer
        try:
            int(value)
            return ["integer", "null"]
        except ValueError:
            pass
        
        # Try float
        try:
            float(value)
            return ["number", "null"]
        except ValueError:
            pass
        
        # Try boolean
        if value.lower() in ["true", "false", "yes", "no", "1", "0"]:
            return ["boolean", "null"]
        
        # Default to string
        return ["string", "null"]

    def _convert_field_value(self, field_name: str, value: Any, schema_properties: Mapping[str, Any]) -> Any:
        """
        Convert field value based on schema type definition.
        
        Args:
            field_name: Name of the field
            value: Raw value from CSV
            schema_properties: Schema properties for type checking
            
        Returns:
            Converted value or None for empty values that should be null
        """
        # Handle None or empty values
        if value is None:
            return None
            
        # Convert to string and strip whitespace
        if isinstance(value, str):
            value = value.strip()
        else:
            value = str(value).strip()
        
        # Handle empty strings
        if value == "":
            return None
            
        # Get field schema definition
        field_schema = schema_properties.get(field_name, {})
        field_types = field_schema.get("type", ["string", "null"])
        
        # Ensure field_types is a list
        if isinstance(field_types, str):
            field_types = [field_types]
            
        # If field can be integer, try to convert
        if "integer" in field_types:
            try:
                # Try to convert to integer
                return int(value)
            except (ValueError, TypeError):
                # If conversion fails and null is allowed, return None
                if "null" in field_types:
                    logging.warning(f"Could not convert '{value}' to integer for field '{field_name}', setting to null")
                    return None
                else:
                    # If null not allowed, keep as string
                    logging.warning(f"Could not convert '{value}' to integer for field '{field_name}', keeping as string")
                    return value
        
        # If field can be number (float), try to convert
        elif "number" in field_types:
            try:
                # Try to convert to float
                return float(value)
            except (ValueError, TypeError):
                # If conversion fails and null is allowed, return None
                if "null" in field_types:
                    logging.warning(f"Could not convert '{value}' to number for field '{field_name}', setting to null")
                    return None
                else:
                    # If null not allowed, keep as string
                    logging.warning(f"Could not convert '{value}' to number for field '{field_name}', keeping as string")
                    return value
        
        # If field can be boolean, try to convert
        elif "boolean" in field_types:
            try:
                # Convert common boolean representations
                lower_value = value.lower()
                if lower_value in ["true", "yes", "1", "on", "enabled"]:
                    return True
                elif lower_value in ["false", "no", "0", "off", "disabled"]:
                    return False
                else:
                    # If conversion fails and null is allowed, return None
                    if "null" in field_types:
                        logging.warning(f"Could not convert '{value}' to boolean for field '{field_name}', setting to null")
                        return None
                    else:
                        # If null not allowed, keep as string
                        return value
            except (ValueError, TypeError):
                if "null" in field_types:
                    return None
                else:
                    return value
        
        # For string fields or any other type, return the cleaned string value
        return value

    def test_connection(self) -> bool:
        """
        Test the connection to the Point API.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Make a test request to the API
            url = f"{self.url_base}{self.path()}"
            headers = self.request_headers()
            params = self.request_params()
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            # Check if request was successful
            if response.status_code == 200:
                # Try to parse the response to ensure it's valid
                json_response = response.json()
                if "Data" in json_response:
                    return True
                    
            logging.error(f"API test failed with status {response.status_code}: {response.text}")
            return False
            
        except Exception as e:
            logging.error(f"Connection test failed: {str(e)}")
            return False