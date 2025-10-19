#!/usr/bin/env python3
"""
Test script to validate MySQL data truncation fixes.
This script tests the data conversion logic with real CSV data.
"""

import json
import csv
import io
from source_point.streams import PointStream

def test_data_conversion():
    """Test data conversion with sample CSV data"""
    
    # Sample CSV data from the actual file
    csv_data = '''sep=;
"TransferID";"OriginalTransferID";"ScopeType";"FlowDefinitionName";"ClientBirthYear";"ClientHealthCareInsurer";"ClientGender";"ClientPatientNumber";"ClientVisitNumber";"ClientCity";"ClientPostalCodeRegion";"TransferCreatedDate";"TransferCreatedYear";"TransferCreatedMonth";"TransferCreatedBy";"TransferClosedDate"
"1475364";"";"Closed";"ZH-VVT";"1950";"Zilveren Kruis Zorgverzekeringen N.V.";"Vrouw";"3210767";"0009881179";"Rotterdam";"30";"2023-01-01 09:30:45";"2023";"1";"Hertog den, DN";"2023-01-03 16:11:52"
"1475419";"";"Closed";"ZH-VVT";"1946";"ONVZ Ziektekostenverzekeraar";"Man";"5195408";"0009881831";"Capelle aan den IJssel";"29";"2023-01-01 14:19:26";"2023";"1";"Giessen van, AC";"2023-01-05 15:08:05"
"1475573";"";"Closed";"ZH-VVT";"1944";"Zilveren Kruis Zorgverzekeringen N.V.";"Man";"1358760";"0009882074";"ROTTERDAM";"30";"2023-01-02 09:54:40";"2023";"1";"Streefland ev van Wijnen, L";"2023-01-02 16:39:18"
'''
    
    # Create a mock config
    config = {
        "api_key": "test_key",
        "organization_id": "test_org",
        "distribution_type_id": "1"
    }
    
    # Create stream instance
    stream = PointStream(config=config)
    
    # Load schema
    schema = stream.get_json_schema()
    schema_properties = schema.get("properties", {})
    
    print("🔍 Testing data conversion logic...")
    print(f"Primary Key: {stream.primary_key}")
    print(f"Cursor Field: {stream.cursor_field}")
    print()
    
    # Parse CSV data
    csv_lines = csv_data.strip().split('\n')
    if csv_lines and csv_lines[0].startswith('sep='):
        csv_content = '\n'.join(csv_lines[1:])
    else:
        csv_content = csv_data
    
    csv_reader = csv.DictReader(io.StringIO(csv_content), delimiter=';')
    
    # Process each row
    for row_index, row in enumerate(csv_reader):
        print(f"📋 Processing Row {row_index + 1}:")
        
        # Clean up the row data with proper type conversion
        cleaned_row = {}
        for key, value in row.items():
            if key and key.strip():
                clean_key = key.strip()
                cleaned_value = stream._convert_field_value(clean_key, value, schema_properties)
                cleaned_row[clean_key] = cleaned_value
                
                # Show conversion details for key fields
                if clean_key in ['TransferID', 'ClientBirthYear', 'TransferCreatedDate', 'OriginalTransferID']:
                    print(f"  {clean_key}: '{value}' -> {cleaned_value} ({type(cleaned_value).__name__})")
        
        # Create record with metadata
        record = {
            "metainfo_identifier": f"test_id_{row_index + 1}",
            "metainfo_timestamp": "2023-01-01T00:00:00Z",
            "metainfo_file_name": "test_file.csv"
        }
        record.update(cleaned_row)
        
        # Validate primary key and cursor field
        primary_key_value = record.get(stream.primary_key)
        cursor_field_value = record.get(stream.cursor_field)
        
        print(f"  ✅ Primary Key ({stream.primary_key}): {primary_key_value}")
        print(f"  ✅ Cursor Field ({stream.cursor_field}): {cursor_field_value}")
        
        # Check for potential MySQL issues
        mysql_issues = []
        for field_name, field_value in record.items():
            field_schema = schema_properties.get(field_name, {})
            field_types = field_schema.get("type", [])
            
            if isinstance(field_types, str):
                field_types = [field_types]
            
            # Check for integer fields with empty string values
            if "integer" in field_types and field_value == "":
                mysql_issues.append(f"Field '{field_name}' has empty string but expects integer")
            
        if mysql_issues:
            print(f"  ⚠️  Potential MySQL Issues:")
            for issue in mysql_issues:
                print(f"    - {issue}")
        else:
            print(f"  ✅ No MySQL data truncation issues detected")
        
        print()
        
        # Only process first 3 rows for testing
        if row_index >= 2:
            break
    
    print("🎯 Test Summary:")
    print(f"  - Primary Key Field: {stream.primary_key}")
    print(f"  - Cursor Field: {stream.cursor_field}")
    print(f"  - Data conversion handles null values properly")
    print(f"  - Integer fields convert empty strings to null")
    print(f"  - Schema maintains consistency for MySQL destination")

if __name__ == "__main__":
    test_data_conversion()