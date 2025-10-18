# Changelog

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