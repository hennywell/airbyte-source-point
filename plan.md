# Airbyte Custom Source Connector Plan
## Point API Connector

### Overview
This plan outlines the development of a custom Airbyte source connector for the Point API. The connector will fetch data from a REST API that returns base64-encoded CSV data and transform it into structured records for Airbyte.

### API Details
- **Base URL**: `https://webservices.point.nl/api/DistributableData/`
- **Endpoint**: `GetLatest`
- **Method**: GET
- **Authentication**: API Key in header and query parameter
- **Response Format**: JSON with base64-encoded CSV data

### API Configuration
Configuration values should be stored in environment variables (see `.env` file):
```json
{
  "APIkey": "${POINT_API_KEY}",
  "OrganizationID": "${POINT_ORGANIZATION_ID}",
  "DistributionTypeID": "1"
}
```

### Response Structure
```json
{
  "status": 200,
  "body": {
    "Identifier": "41cae7a8-b4d7-4b05-9f6e-3fe7d6ebc9a3",
    "FileName": "csvdump-603-20251018125125.csv",
    "ContentType": "text/csv",
    "Timestamp": "2025-10-18T12:51:36.21",
    "Data": "base64_encoded_csv_string"
  }
}
```

## Development Plan

### Phase 1: Project Setup and Structure
**Goal**: Establish proper Airbyte connector project structure

#### 1.1 Initialize Project Structure
```
source-point/
├── source_point/
│   ├── __init__.py
│   ├── source.py
│   ├── streams.py
│   └── schemas/
│       ├── api_response.json
│       └── transfer_data.json
├── unit_tests/
├── integration_tests/
├── acceptance-test-config.yml
├── pyproject.toml
├── metadata.yaml
├── Dockerfile
├── README.md
├── CHANGELOG.md
└── docs/
    └── source-point.md
```

#### 1.2 Development Environment Setup
- Install Python 3.9+ with Poetry
- Install Airbyte CDK: `pip install airbyte-cdk`
- Set up virtual environment
- Configure IDE/editor for Python development

### Phase 2: Connector Specification
**Goal**: Define connector configuration schema and validation

#### 2.1 Create Connector Specification
Define configuration schema in `source.py`:
```python
def spec(self) -> AirbyteConnectionSpecification:
    return AirbyteConnectionSpecification(
        connectionSpecification={
            "type": "object",
            "required": ["api_key", "organization_id"],
            "properties": {
                "api_key": {
                    "type": "string",
                    "title": "API Key",
                    "description": "Your Point API key",
                    "airbyte_secret": True
                },
                "organization_id": {
                    "type": "string",
                    "title": "Organization ID",
                    "description": "Your organization identifier",
                    "examples": ["${POINT_ORGANIZATION_ID}"]
                },
                "distribution_type_id": {
                    "type": "string",
                    "title": "Distribution Type ID",
                    "description": "Distribution type identifier",
                    "default": "1"
                }
            }
        }
    )
```

### Phase 3: Core Implementation
**Goal**: Implement the main connector logic

#### 3.1 AbstractSource Implementation
Create main source class inheriting from `AbstractSource`:
```python
class SourcePoint(AbstractSource):
    def check_connection(self, logger: logging.Logger, config: Mapping[str, Any]) -> Tuple[bool, Optional[Any]]:
        # Validate API credentials and connectivity
        
    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        # Return list of available streams
```

#### 3.2 HttpStream Implementation
Create stream class for API interaction:
```python
class PointStream(HttpStream):
    url_base = "https://webservices.point.nl/api/DistributableData/"
    primary_key = None  # No primary key for this data
    
    def path(self, **kwargs) -> str:
        return "GetLatest"
    
    def request_headers(self, **kwargs) -> Mapping[str, str]:
        return {"APIkey": self.config["api_key"]}
    
    def request_params(self, **kwargs) -> Mapping[str, Any]:
        return {
            "OrganizationID": self.config["organization_id"],
            "DistributionTypeID": self.config.get("distribution_type_id", "1"),
            "APIkey": self.config["api_key"]
        }
    
    def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping[str, Any]]:
        # Decode base64 data and parse CSV
```

#### 3.3 Data Processing Logic
Implement base64 decoding and CSV parsing:
- Decode base64 `Data` field from API response
- Parse CSV with semicolon delimiter
- Transform CSV rows into JSON records
- Include API metadata (Identifier, FileName, Timestamp) with each record

### Phase 4: Schema Definition
**Goal**: Define proper JSON schemas for data validation

#### 4.1 API Response Schema
Create schema for the API response structure in `schemas/api_response.json`

#### 4.2 Transfer Data Schema
Create comprehensive schema for CSV data in `schemas/transfer_data.json`:
- All 100+ CSV columns properly typed
- Date fields as date-time format
- Numeric fields as integers/numbers
- Text fields as strings
- Boolean fields where applicable

### Phase 5: Testing Strategy
**Goal**: Ensure connector reliability and correctness

#### 5.1 Unit Tests
- Test connection validation
- Test API request building
- Test base64 decoding
- Test CSV parsing logic
- Test error handling scenarios
- Mock external API calls

#### 5.2 Integration Tests
- Test with real API responses (using credentials from .env file)
- Validate complete data flow
- Test error scenarios (invalid credentials, network issues)

#### 5.3 Connector Acceptance Tests (CAT)
Configure `acceptance-test-config.yml`:
```yaml
connector_image: airbyte/source-point:dev
test_strictness_level: high
acceptance_tests:
  spec:
    tests:
      - spec_path: "source_point/spec.yaml"
  connection:
    tests:
      - config_path: "secrets/config.json"  # Load from .env variables
  discovery:
    tests:
      - config_path: "secrets/config.json"  # Load from .env variables
  basic_read:
    tests:
      - config_path: "secrets/config.json"  # Load from .env variables
        configured_catalog_path: "integration_tests/configured_catalog.json"
```

### Phase 6: Documentation
**Goal**: Create comprehensive user and developer documentation

#### 6.1 User Documentation
Create `docs/source-point.md` following Airbyte standards:
- Prerequisites section
- Setup guide for Airbyte Cloud and Open Source
- Configuration parameters
- Supported sync modes
- Data schema documentation
- Troubleshooting guide
- Changelog

#### 6.2 Developer Documentation
- README.md with development setup
- Code comments and docstrings
- Architecture decisions

### Phase 7: Packaging and Metadata
**Goal**: Proper connector packaging for distribution

#### 7.1 Poetry Configuration
Configure `pyproject.toml`:
```toml
[tool.poetry]
name = "source-point"
version = "0.1.0"
description = "Source implementation for Point API"
authors = ["Your Name <your.email@example.com>"]
license = "MIT"

[tool.poetry.dependencies]
python = "^3.9"
airbyte-cdk = "^1.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0.0"
pytest-mock = "^3.10.0"
```

#### 7.2 Metadata Configuration
Configure `metadata.yaml`:
```yaml
data:
  connectorSubtype: api
  connectorType: source
  definitionId: uuid-for-point
  dockerImageTag: 0.1.0
  dockerRepository: airbyte/source-point
  githubIssueLabel: source-point
  name: Point
  registries:
    cloud:
      enabled: false
    oss:
      enabled: true
  releaseStage: alpha
  supportLevel: community
  tags:
    - language:python
    - cdk:python
  connectorTestSuitesOptions:
    - suite: unitTests
    - suite: integrationTests
    - suite: acceptanceTests
```

### Phase 8: Docker Configuration
**Goal**: Containerize the connector for deployment

#### 8.1 Dockerfile
Since this is a Python connector, use the standard base image approach:
```yaml
# In metadata.yaml
connectorBuildOptions:
  baseImage: docker.io/airbyte/python-connector-base:1.2.0
```

### Phase 9: Local Testing
**Goal**: Validate connector works with Airbyte

#### 9.1 Local Development Testing
```bash
# Build connector
airbyte-ci connectors --name=source-point build

# Run tests
airbyte-ci connectors --name=source-point test

# Test specific commands (ensure .env is loaded)
python -m source_point spec
python -m source_point check --config secrets/config.json
python -m source_point discover --config secrets/config.json
python -m source_point read --config secrets/config.json --catalog catalog.json
```

#### 9.2 Integration with Local Airbyte
- Deploy connector to local Airbyte instance
- Create source configuration
- Test data synchronization
- Validate data quality and completeness

### Phase 10: Deployment and Distribution
**Goal**: Make connector available for production use

#### 10.1 Version Control and CI/CD
- Set up Git repository
- Configure GitHub Actions for automated testing
- Set up automated builds and releases

#### 10.2 Distribution Options
1. **Docker Registry**: Push to Docker Hub or private registry
2. **PyPI**: Publish as Python package
3. **Airbyte Marketplace**: Submit for inclusion in official catalog

#### 10.3 Production Deployment
- Build production Docker image
- Deploy to container registry
- Configure in production Airbyte instance
- Monitor and maintain

## Technical Considerations

### Data Processing Strategy
1. **API Response Handling**: Parse JSON response and extract metadata
2. **Base64 Decoding**: Decode the `Data` field containing CSV content
3. **CSV Processing**: Parse semicolon-delimited CSV with proper escaping
4. **Record Enrichment**: Add API metadata to each CSV record
5. **Schema Validation**: Ensure all records conform to defined schema

### Error Handling
- Network connectivity issues
- API authentication failures
- Invalid base64 data
- Malformed CSV content
- Rate limiting and retry logic

### Performance Considerations
- Memory-efficient CSV processing for large files
- Streaming data processing to avoid memory issues
- Proper connection pooling and timeouts

### Security
- Secure handling of API keys
- No logging of sensitive data
- Proper input validation and sanitization

## Quality Assurance Checklist

### Code Quality
- [ ] Follows Airbyte Python CDK patterns
- [ ] Proper error handling and logging
- [ ] Type hints and documentation
- [ ] Code formatting with Black/isort
- [ ] Linting with flake8/pylint

### Testing Coverage
- [ ] Unit tests for all major functions
- [ ] Integration tests with real API
- [ ] Connector Acceptance Tests passing
- [ ] Error scenario testing
- [ ] Performance testing with large datasets

### Documentation
- [ ] User documentation follows Airbyte standards
- [ ] All configuration options documented
- [ ] Troubleshooting guide included
- [ ] Changelog maintained
- [ ] Code properly commented

### Compliance
- [ ] Follows Airbyte QA checks
- [ ] Proper licensing (MIT)
- [ ] Security best practices
- [ ] Performance requirements met
- [ ] Metadata properly configured

This comprehensive plan ensures the connector will be production-ready, maintainable, and compliant with Airbyte standards.