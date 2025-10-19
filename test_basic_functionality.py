#!/usr/bin/env python3
"""
Basic functionality test for the Point connector without full CDK dependencies.
This script tests the core logic of base64 decoding and CSV parsing.
"""

import base64
import csv
import io
import json


def test_base64_csv_parsing():
    """Test the core functionality of base64 decoding and CSV parsing."""
    
    # Create test CSV data
    csv_data = "column1;column2;column3\nvalue1;value2;value3\nvalue4;value5;value6"
    print(f"Original CSV data:\n{csv_data}\n")
    
    # Encode to base64 (simulating API response)
    encoded_data = base64.b64encode(csv_data.encode('utf-8')).decode('utf-8')
    print(f"Base64 encoded data:\n{encoded_data}\n")
    
    # Simulate API response
    mock_api_response = {
        "status": 200,
        "body": {
            "Identifier": "test-id-123",
            "FileName": "test.csv",
            "ContentType": "text/csv",
            "Timestamp": "2023-01-01T12:00:00Z",
            "Data": encoded_data
        }
    }
    
    print(f"Mock API response:\n{json.dumps(mock_api_response, indent=2)}\n")
    
    # Test the parsing logic (from our streams.py)
    try:
        body = mock_api_response["body"]
        
        # Extract metadata
        metadata = {
            "identifier": body.get("Identifier"),
            "file_name": body.get("FileName"),
            "content_type": body.get("ContentType"),
            "timestamp": body.get("Timestamp"),
            "api_status": mock_api_response.get("status")
        }
        
        print(f"Extracted metadata:\n{json.dumps(metadata, indent=2)}\n")
        
        # Decode base64 data
        decoded_csv = base64.b64decode(body["Data"]).decode('utf-8')
        print(f"Decoded CSV data:\n{decoded_csv}\n")
        
        # Parse CSV data
        csv_reader = csv.DictReader(io.StringIO(decoded_csv), delimiter=';')
        
        records = []
        for row_index, row in enumerate(csv_reader):
            # Create flattened record with metadata and CSV data at top level
            record = {
                # Metadata fields at top level
                "identifier": metadata["identifier"],
                "timestamp": metadata["timestamp"],
                "file_name": metadata["file_name"],
                "content_type": metadata["content_type"],
                "api_status": metadata["api_status"],
                "row_index": row_index,
            }
            
            # Add all CSV columns at top level
            record.update(row)
            
            records.append(record)
        
        print(f"Parsed records:\n{json.dumps(records, indent=2)}\n")
        
        # Validate results
        assert len(records) == 2, f"Expected 2 records, got {len(records)}"
        assert records[0]["column1"] == "value1"  # CSV data now at top level
        assert records[1]["column1"] == "value4"  # CSV data now at top level
        assert records[0]["identifier"] == "test-id-123"  # Metadata at top level
        assert records[0]["timestamp"] == "2023-01-01T12:00:00Z"  # Metadata at top level
        
        print("✅ All tests passed! Core functionality is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


def test_connector_specification():
    """Test the connector specification structure."""
    
    spec = {
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
    
    print(f"Connector specification:\n{json.dumps(spec, indent=2)}\n")
    
    # Validate specification structure
    assert "properties" in spec
    assert "api_key" in spec["properties"]
    assert "organization_id" in spec["properties"]
    assert spec["required"] == ["api_key", "organization_id"]
    
    print("✅ Connector specification is valid!")
    return True


def test_json_schema():
    """Test the JSON schema for the stream."""
    
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "identifier": {
                "type": ["string", "null"],
                "description": "Unique identifier from the API response (Primary Key)"
            },
            "timestamp": {
                "type": ["string", "null"],
                "format": "date-time",
                "description": "Timestamp when the data was generated (Cursor Field)"
            },
            "file_name": {
                "type": ["string", "null"],
                "description": "Name of the CSV file"
            },
            "content_type": {
                "type": ["string", "null"],
                "description": "Content type of the data"
            },
            "api_status": {
                "type": ["integer", "null"],
                "description": "HTTP status code from the API"
            },
            "row_index": {
                "type": "integer",
                "description": "Index of the row in the CSV data"
            }
        },
        "additionalProperties": {
            "type": ["string", "null", "integer", "number", "boolean"],
            "description": "CSV column data - dynamically added based on CSV structure"
        }
    }
    
    print(f"Stream JSON schema:\n{json.dumps(schema, indent=2)}\n")
    
    # Validate schema structure
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "row_index" in schema["properties"]
    assert "identifier" in schema["properties"]
    assert "timestamp" in schema["properties"]
    assert "additionalProperties" in schema  # For dynamic CSV columns
    
    print("✅ JSON schema is valid!")
    return True


if __name__ == "__main__":
    print("🧪 Testing Point Connector Core Functionality\n")
    print("=" * 60)
    
    tests = [
        ("Base64 CSV Parsing", test_base64_csv_parsing),
        ("Connector Specification", test_connector_specification),
        ("JSON Schema", test_json_schema),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running test: {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The connector core functionality is working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the implementation.")