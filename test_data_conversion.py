#!/usr/bin/env python3
"""
Test script to validate the data conversion logic for the Point connector.
This script tests the fix for MySQL data truncation errors.
"""

import json
import os
import sys

# Add the source_point directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'source_point'))

from streams import PointStream

def test_field_conversion():
    """Test the _convert_field_value method with various scenarios"""
    
    # Create a mock config for the stream
    config = {
        "api_key": "test_key",
        "organization_id": "test_org"
    }
    
    # Create stream instance
    stream = PointStream(config)
    
    # Load the actual schema
    schema_path = os.path.join("source_point", "schemas", "point_data.json")
    with open(schema_path, "r") as f:
        schema = json.load(f)
    
    schema_properties = schema.get("properties", {})
    
    # Test cases for integer fields
    test_cases = [
        # (field_name, input_value, expected_output, description)
        ("TransferID", "", None, "Empty string should become None for integer field"),
        ("TransferID", "123", 123, "Valid integer string should convert to int"),
        ("TransferID", "abc", None, "Invalid integer should become None when null allowed"),
        ("ClientBirthYear", "1990", 1990, "Birth year should convert to integer"),
        ("ClientBirthYear", "", None, "Empty birth year should become None"),
        ("ClientPatientNumber", "12345", 12345, "Patient number should convert to integer"),
        ("ClientBSN", "", None, "Empty BSN should become None"),
        ("ClientBSN", "123456789", 123456789, "Valid BSN should convert to integer"),
        
        # Test cases for string fields
        ("ClientFirstName", "", None, "Empty string should become None"),
        ("ClientFirstName", "John", "John", "Valid string should remain string"),
        ("ClientFirstName", "  John  ", "John", "String should be trimmed"),
        
        # Test cases for metainfo fields
        ("metainfo_identifier", "ID123", "ID123", "Metainfo identifier should remain string"),
        ("metainfo_timestamp", "2024-01-01T00:00:00Z", "2024-01-01T00:00:00Z", "Metainfo timestamp should remain string"),
    ]
    
    print("Testing data conversion logic...")
    print("=" * 60)
    
    all_passed = True
    
    for field_name, input_value, expected_output, description in test_cases:
        try:
            result = stream._convert_field_value(field_name, input_value, schema_properties)
            
            if result == expected_output:
                print(f"✅ PASS: {description}")
                print(f"   Field: {field_name}, Input: '{input_value}' -> Output: {result}")
            else:
                print(f"❌ FAIL: {description}")
                print(f"   Field: {field_name}, Input: '{input_value}' -> Expected: {expected_output}, Got: {result}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ ERROR: {description}")
            print(f"   Field: {field_name}, Input: '{input_value}' -> Exception: {str(e)}")
            all_passed = False
        
        print()
    
    print("=" * 60)
    if all_passed:
        print("🎉 All tests passed! The data conversion logic should fix the MySQL truncation error.")
    else:
        print("⚠️  Some tests failed. Please review the conversion logic.")
    
    return all_passed

def test_problematic_scenario():
    """Test the specific scenario that was causing MySQL errors"""
    
    print("\nTesting the specific MySQL error scenario...")
    print("=" * 60)
    
    # Create a mock config for the stream
    config = {
        "api_key": "test_key", 
        "organization_id": "test_org"
    }
    
    # Create stream instance
    stream = PointStream(config)
    
    # Load the actual schema
    schema_path = os.path.join("source_point", "schemas", "point_data.json")
    with open(schema_path, "r") as f:
        schema = json.load(f)
    
    schema_properties = schema.get("properties", {})
    
    # Simulate a CSV row with empty values for integer fields (the problematic scenario)
    problematic_row = {
        "TransferID": "",  # This was causing "Truncated incorrect INTEGER value: ''"
        "ClientBirthYear": "",
        "ClientPatientNumber": "",
        "ClientBSN": "",
        "ClientFirstName": "John",
        "ClientLastName": "Doe",
        "OriginalTransferID": "ABC123"
    }
    
    print("Original problematic row:")
    for key, value in problematic_row.items():
        print(f"  {key}: '{value}'")
    
    print("\nAfter conversion:")
    converted_row = {}
    for key, value in problematic_row.items():
        converted_value = stream._convert_field_value(key, value, schema_properties)
        if converted_value is not None:
            converted_row[key] = converted_value
        print(f"  {key}: '{value}' -> {converted_value}")
    
    print(f"\nFinal record (only non-null values):")
    for key, value in converted_row.items():
        print(f"  {key}: {value} ({type(value).__name__})")
    
    # Check that no empty strings remain for integer fields
    integer_fields = ["TransferID", "ClientBirthYear", "ClientPatientNumber", "ClientBSN"]
    has_empty_integers = False
    
    for field in integer_fields:
        if field in converted_row and converted_row[field] == "":
            print(f"❌ ERROR: Field '{field}' still contains empty string!")
            has_empty_integers = True
    
    if not has_empty_integers:
        print("✅ SUCCESS: No empty strings remain for integer fields!")
        print("✅ This should resolve the MySQL 'Truncated incorrect INTEGER value' error.")
    
    return not has_empty_integers

if __name__ == "__main__":
    print("Point Connector - Data Conversion Test")
    print("Testing fix for MySQL data truncation errors")
    print()
    
    # Run the tests
    conversion_test_passed = test_field_conversion()
    scenario_test_passed = test_problematic_scenario()
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    if conversion_test_passed and scenario_test_passed:
        print("🎉 ALL TESTS PASSED!")
        print("The fix should resolve the MySQL data truncation error.")
        print("\nNext steps:")
        print("1. Build and deploy the updated connector")
        print("2. Test with a real sync to MySQL destination")
    else:
        print("⚠️  SOME TESTS FAILED!")
        print("Please review and fix the issues before deploying.")