# Changelog

## 0.2.1
2025-10-19 - MySQL data truncation fixes and metadata field naming updates

### Bug Fixes
- Fix MySQL 'Truncated incorrect INTEGER value' error by ensuring empty strings are converted to NULL for integer fields
- Resolve MySQL data truncation issues that were causing sync failures after ~13,813 records

### Breaking Changes
- Update metadata field naming from `metainfo_*` to `_metadata_*` format
- Schema field names updated:
  - `metainfo_identifier` → `_metadata_identifier`
  - `metainfo_timestamp` → `_metadata_timestamp`
  - `metainfo_file_name` → `_metadata_file_name`

### Enhancements
- Add comprehensive MySQL injection testing to validate fixes
- Add mysql-connector-python dependency for testing
- Improved data type conversion logic with schema-aware field handling
- Enhanced error handling for database compatibility

### Technical Details
- All unit tests passing (19/19)
- Validated with direct MySQL database injection tests
- Docker images: ghcr.io/hennywell/airbyte-source-point:0.2.1, ghcr.io/hennywell/airbyte-source-point:latest

## 0.2.0
2025-10-19 - Primary key and cursor field improvements

### Breaking Changes
- Update primary key from `metainfo_identifier` to `TransferID` for better uniqueness
- Change cursor field from `metainfo_timestamp` to `TransferCreatedDate` for accurate incremental sync

### Bug Fixes
- Fix primary key null errors due to non-unique metainfo_identifier values
- Resolve MySQL data truncation by properly converting empty strings to null for INTEGER fields
- Fix inconsistent schema structure causing destination compatibility issues

### Enhancements
- Maintain schema consistency by including all fields in records
- Update unit tests to reflect new primary key and cursor field configuration
- Improved incremental sync reliability

### Technical Details
- All tests passing (19/19) ✅
- Enhanced data validation and type conversion

## 0.1.9
2025-10-19 - Schema-aware data conversion and MySQL compatibility

### Bug Fixes
- Fix MySQL 'Truncated incorrect INTEGER value' errors through proper data type conversion
- Convert empty strings to null for integer fields to prevent database truncation errors

### Enhancements
- Add schema-aware data type conversion in parse_response() method
- Add _convert_field_value() helper for proper type handling (integer, number, boolean, string)
- Add comprehensive test suite for data conversion logic

### Schema Changes
- Remove content_type, api_status, row_index fields
- Add metainfo_ prefix to identifier, timestamp, file_name fields

### Technical Details
- Resolves sync failure issue affecting ~13,813 records
- Enhanced data validation and type safety

## 0.1.8
2025-10-19 - Enhanced schema discovery and CSV parsing

### New Features
- Add dynamic schema discovery from API responses
- Expand JSON schema with comprehensive field definitions
- Support for automatic column detection from CSV data

### Enhancements
- Improve CSV parsing and data transformation capabilities
- Enhanced error handling for schema discovery
- Better handling of varying CSV structures
- Improved schema inference capabilities

### Technical Details
- Significantly improved connector's ability to handle varying CSV structures
- Enhanced data processing pipeline

## 0.1.6
2025-10-19 - Version update and improvements

### Enhancements
- General improvements and optimizations
- Updated version tracking

## 0.1.0
2024-01-01 - Initial release of Point source connector

### New Features
- Initial implementation of Point API source connector
- Support for fetching base64-encoded CSV data from Point API
- Automatic decoding and parsing of CSV data into structured records
- Full refresh sync mode support
- Comprehensive error handling and logging
- Unit and integration test coverage
- Complete documentation and setup guides

### API Support
- GetLatest endpoint integration
- API key authentication
- Organization ID and Distribution Type ID configuration
- Semicolon-delimited CSV parsing
- Metadata enrichment for each record

### Technical Details
- Built with Airbyte CDK for Python
- Follows Airbyte connector development best practices
- Comprehensive test suite including unit, integration, and acceptance tests
- Docker containerization support
- Poetry dependency management