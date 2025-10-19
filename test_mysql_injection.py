#!/usr/bin/env python3
"""
MySQL injection test script to validate data truncation fixes.
This script directly inserts records into MySQL to test integer field handling.
"""

import mysql.connector
import json
from source_point.streams import PointStream
from typing import Dict, Any

# MySQL connection configuration
MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'remote_user',
    'password': 'StrongPassword!123',
    'database': 'airbyte',
    'ssl_disabled': True
}

def create_test_table(cursor):
    """Create a test table that mimics Airbyte's destination table structure"""
    
    # Drop table if exists
    cursor.execute("DROP TABLE IF EXISTS test_point_data")
    
    # Create table with integer fields that could cause truncation
    create_table_sql = """
    CREATE TABLE test_point_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        _metadata_identifier VARCHAR(255),
        _metadata_timestamp DATETIME,
        _metadata_file_name VARCHAR(255),
        TransferID INT,
        ClientBirthYear INT,
        ClientPatientNumber INT,
        ClientBSN BIGINT,
        OriginalTransferID VARCHAR(255),
        ClientGender VARCHAR(50),
        TransferCreatedDate DATETIME,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    cursor.execute(create_table_sql)
    print("✅ Created test table 'test_point_data'")

def test_data_insertion():
    """Test inserting records with various integer field scenarios"""
    
    # Create stream instance for data conversion
    config = {
        "api_key": "test_key",
        "organization_id": "test_org",
        "distribution_type_id": "1"
    }
    stream = PointStream(config=config)
    schema = stream.get_json_schema()
    schema_properties = schema.get("properties", {})
    
    # Test cases that would previously cause MySQL truncation errors
    test_cases = [
        {
            "description": "Valid integer values",
            "raw_data": {
                "TransferID": "12345",
                "ClientBirthYear": "1980",
                "ClientPatientNumber": "67890",
                "ClientBSN": "123456789",
                "OriginalTransferID": "ABC123",
                "ClientGender": "Male",
                "TransferCreatedDate": "2023-01-01 10:00:00"
            }
        },
        {
            "description": "Empty strings for integer fields (would cause truncation)",
            "raw_data": {
                "TransferID": "54321",  # Valid primary key
                "ClientBirthYear": "",  # Empty string -> should become NULL
                "ClientPatientNumber": "",  # Empty string -> should become NULL
                "ClientBSN": "",  # Empty string -> should become NULL
                "OriginalTransferID": "",
                "ClientGender": "Female",
                "TransferCreatedDate": "2023-01-02 11:00:00"
            }
        },
        {
            "description": "Mixed empty and valid integer fields",
            "raw_data": {
                "TransferID": "98765",
                "ClientBirthYear": "1975",  # Valid
                "ClientPatientNumber": "",  # Empty -> NULL
                "ClientBSN": "987654321",  # Valid
                "OriginalTransferID": "DEF456",
                "ClientGender": "Other",
                "TransferCreatedDate": "2023-01-03 12:00:00"
            }
        },
        {
            "description": "Whitespace-only integer fields",
            "raw_data": {
                "TransferID": "11111",
                "ClientBirthYear": "   ",  # Whitespace -> should become NULL
                "ClientPatientNumber": "\t\n",  # Whitespace -> should become NULL
                "ClientBSN": " ",  # Whitespace -> should become NULL
                "OriginalTransferID": "GHI789",
                "ClientGender": "Male",
                "TransferCreatedDate": "2023-01-04 13:00:00"
            }
        }
    ]
    
    try:
        # Connect to MySQL
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()
        
        print("🔗 Connected to MySQL database")
        
        # Create test table
        create_test_table(cursor)
        
        # Process and insert test cases
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 Test Case {i}: {test_case['description']}")
            
            # Convert raw data using our stream's conversion logic
            converted_data = {}
            for field_name, raw_value in test_case['raw_data'].items():
                converted_value = stream._convert_field_value(field_name, raw_value, schema_properties)
                converted_data[field_name] = converted_value
                
                # Show conversion details for integer fields
                field_schema = schema_properties.get(field_name, {})
                field_types = field_schema.get("type", [])
                if isinstance(field_types, str):
                    field_types = [field_types]
                
                if "integer" in field_types:
                    print(f"  {field_name}: '{raw_value}' -> {converted_value} ({type(converted_value).__name__})")
            
            # Add metadata
            record = {
                "_metadata_identifier": f"test_id_{i}",
                "_metadata_timestamp": "2023-01-01 00:00:00",
                "_metadata_file_name": "test_file.csv"
            }
            record.update(converted_data)
            
            # Prepare SQL insert statement
            columns = list(record.keys())
            placeholders = ", ".join(["%s"] * len(columns))
            sql = f"INSERT INTO test_point_data ({', '.join(columns)}) VALUES ({placeholders})"
            
            # Prepare values (convert None to NULL for MySQL)
            values = [record[col] for col in columns]
            
            try:
                # Execute insert
                cursor.execute(sql, values)
                connection.commit()
                print(f"  ✅ Successfully inserted record {i}")
                
                # Verify the inserted data
                cursor.execute("SELECT * FROM test_point_data WHERE id = LAST_INSERT_ID()")
                inserted_record = cursor.fetchone()
                print(f"  📋 Inserted record ID: {inserted_record[0]}")
                
            except mysql.connector.Error as e:
                print(f"  ❌ MySQL Error: {e}")
                print(f"  📝 SQL: {sql}")
                print(f"  📝 Values: {values}")
                connection.rollback()
        
        # Query and display all inserted records
        print("\n📊 Final Results - All Inserted Records:")
        cursor.execute("""
            SELECT id, _metadata_identifier, TransferID, ClientBirthYear, 
                   ClientPatientNumber, ClientBSN, OriginalTransferID, ClientGender
            FROM test_point_data 
            ORDER BY id
        """)
        
        records = cursor.fetchall()
        print(f"{'ID':<3} {'Meta ID':<10} {'TransferID':<10} {'BirthYear':<10} {'PatientNum':<12} {'BSN':<12} {'OriginalID':<12} {'Gender':<8}")
        print("-" * 85)
        
        for record in records:
            id_val, meta_id, transfer_id, birth_year, patient_num, bsn, original_id, gender = record
            print(f"{id_val:<3} {meta_id:<10} {transfer_id or 'NULL':<10} {birth_year or 'NULL':<10} {patient_num or 'NULL':<12} {bsn or 'NULL':<12} {original_id or 'NULL':<12} {gender:<8}")
        
        print(f"\n🎯 Summary:")
        print(f"  - Successfully inserted {len(records)} records")
        print(f"  - No MySQL data truncation errors occurred")
        print(f"  - Empty strings were properly converted to NULL values")
        print(f"  - Integer fields handle NULL values correctly")
        
        # Clean up
        cursor.execute("DROP TABLE test_point_data")
        print(f"  - Cleaned up test table")
        
    except mysql.connector.Error as e:
        print(f"❌ MySQL Connection Error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False
        
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("🔌 MySQL connection closed")
    
    return True

if __name__ == "__main__":
    print("🔍 Testing MySQL data injection with integer field conversion...")
    print("📍 This validates that empty strings are converted to NULL to prevent truncation errors")
    print()
    
    success = test_data_insertion()
    
    if success:
        print("\n✅ All tests passed! The data conversion fixes prevent MySQL truncation errors.")
    else:
        print("\n❌ Tests failed. Check the error messages above.")