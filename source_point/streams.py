#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#

import base64
import csv
import io
import json
import logging
import os
from typing import Any, Iterable, Mapping, Optional

import requests
from airbyte_cdk.sources.streams.http import HttpStream


class PointStream(HttpStream):
    """
    Stream implementation for Point API.
    
    This stream fetches data from the Point API, which returns base64-encoded CSV data,
    and transforms it into structured records.
    """

    url_base = "https://webservices.verzorgdeoverdracht.nl/api/DistributableData/"
    primary_key = None  # No primary key for this data
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

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        """
        Return the next page token for pagination.
        
        Since the Point API returns all data in a single response,
        there is no pagination, so we always return None.
        """
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
                "identifier": json_response.get("Identifier"),
                "file_name": json_response.get("FileName"),
                "content_type": json_response.get("ContentType"),
                "timestamp": json_response.get("Timestamp"),
                "api_status": response.status_code
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
            
            for row_index, row in enumerate(csv_reader):
                # Clean up the row data - remove empty keys and null values
                cleaned_row = {}
                for key, value in row.items():
                    if key and key.strip() and value is not None:
                        cleaned_row[key.strip()] = value.strip() if isinstance(value, str) else value
                
                # Create record with CSV data and metadata
                record = {
                    "row_index": row_index,
                    "metadata": metadata,
                    "data": cleaned_row
                }
                yield record
                
        except Exception as e:
            logging.error(f"Error parsing response: {str(e)}")
            raise

    def get_json_schema(self) -> Mapping[str, Any]:
        """
        Return the JSON schema for this stream.
        """
        schema_path = os.path.join(os.path.dirname(__file__), "schemas", "point_data.json")
        try:
            with open(schema_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            # Fallback schema if file not found
            return {
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
                            "identifier": {
                                "type": ["string", "null"],
                                "description": "Unique identifier from the API response"
                            },
                            "file_name": {
                                "type": ["string", "null"],
                                "description": "Name of the CSV file"
                            },
                            "content_type": {
                                "type": ["string", "null"],
                                "description": "Content type of the data"
                            },
                            "timestamp": {
                                "type": ["string", "null"],
                                "format": "date-time",
                                "description": "Timestamp when the data was generated"
                            },
                            "api_status": {
                                "type": ["integer", "null"],
                                "description": "HTTP status code from the API"
                            }
                        }
                    },
                    "data": {
                        "type": "object",
                        "description": "CSV row data as key-value pairs",
                        "additionalProperties": {
                            "type": ["string", "null"]
                        }
                    }
                }
            }

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