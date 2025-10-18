# Point Source Connector

This is the repository for the Point source connector, written in Python.
For information about how to use this connector within Airbyte, see [the documentation](https://docs.airbyte.com/integrations/sources/point).

## 🚀 Quick Start with GitHub Container Registry

The easiest way to use this connector is via GitHub Container Registry:

1. **Push this code to a GitHub repository**
2. **GitHub Actions will automatically build and publish the Docker image**
3. **Use the image in Airbyte**: `ghcr.io/YOUR_USERNAME/YOUR_REPO_NAME:latest`

📖 **See [GITHUB_DEPLOYMENT_GUIDE.md](GITHUB_DEPLOYMENT_GUIDE.md) for complete setup instructions**

## 📋 Deployment Options

- **🐙 [GitHub Container Registry](GITHUB_DEPLOYMENT_GUIDE.md)** - Automated builds (Recommended)
- **🏠 [Local Development](LOCAL_DEPLOYMENT_GUIDE.md)** - Docker Compose & Kubernetes
- **🏭 Manual Docker Build** - See sections below

## Local development

### Prerequisites
* Python 3.9+
* Poetry for dependency management
* Docker (for building and testing)

### Installing the connector
From this connector directory, run:
```bash
poetry install
```

### Create credentials
**If you are a community contributor**, follow the instructions in the [documentation](https://docs.airbyte.com/integrations/sources/point)
to generate the necessary credentials. Then create a file `secrets/config.json` conforming to the `source_point/spec.yaml` file.
Note that any directory named `secrets` is gitignored across the entire Airbyte repo, so there is no danger of accidentally checking in sensitive information.
See `integration_tests/sample_config.json` for a sample config file.

**If you are an Airbyte core member**, copy the credentials in Lastpass under the secret name `source point test creds`
and place them into `secrets/config.json`.

### Locally running the connector
```
python -m source_point spec
python -m source_point check --config secrets/config.json
python -m source_point discover --config secrets/config.json
python -m source_point read --config secrets/config.json --catalog integration_tests/configured_catalog.json
```

### Running unit tests
To run unit tests locally, from the connector directory run:
```
poetry run pytest unit_tests
```

### Building the docker image
1. Build a docker image:
```
docker build . --tag airbyte/source-point:dev
```

2. Run the connector:
```
docker run --rm airbyte/source-point:dev spec
docker run --rm -v $(pwd)/secrets:/secrets airbyte/source-point:dev check --config /secrets/config.json
docker run --rm -v $(pwd)/secrets:/secrets airbyte/source-point:dev discover --config /secrets/config.json
docker run --rm -v $(pwd)/secrets:/secrets -v $(pwd)/integration_tests:/integration_tests airbyte/source-point:dev read --config /secrets/config.json --catalog /integration_tests/configured_catalog.json
```

## Testing
Make sure to familiarize yourself with [pytest test discovery](https://docs.pytest.org/en/latest/goodpractices.html#test-discovery) to know how your test files and methods should be named.
First install test dependencies into your virtual environment:
```
poetry install --with dev
```

### Unit Tests
To run unit tests:
```
poetry run pytest unit_tests
```

### Integration Tests
There are two types of integration tests: Acceptance Tests and custom integration tests.

#### Custom Integration tests
Place custom tests inside `integration_tests/` folder, then, from the connector root, run
```
poetry run pytest integration_tests
```

#### Acceptance Tests
Customize `acceptance-test-config.yml` file to configure tests. See [Connector Acceptance Tests](https://docs.airbyte.com/connector-development/testing-connectors/connector-acceptance-tests-reference) for more information.
If your connector requires to create or destroy resources for use during acceptance tests create fixtures for it and place them inside integration_tests/acceptance.py.

To run your integration tests with acceptance tests, from the connector root, run
```
airbyte-ci connectors --name=source-point test
```

### Using airbyte-ci
You can also use [airbyte-ci](https://github.com/airbytehq/airbyte/blob/master/airbyte-ci/connectors/pipelines/README.md) to test the connector:

```bash
airbyte-ci connectors --name=source-point build
airbyte-ci connectors --name=source-point test
```

## Dependency Management
All of this connector's dependencies should go in `pyproject.toml`. Please commit the changes to `poetry.lock`.

## Publishing a new version of the connector
You've checked out the repo, implemented a million dollar feature, and you're ready to share your changes with the world. Now what?
1. Make sure your changes are passing our test suite: `airbyte-ci connectors --name=source-point test`
2. Bump the connector version in `metadata.yaml`: increment the `dockerImageTag` value. Please follow [semantic versioning for connectors](https://docs.airbyte.com/contributing-to-airbyte/#semantic-versioning-for-connectors).
3. Make sure the `metadata.yaml` content is up to date.
4. Make the connector documentation and its changelog is up to date (`docs/integrations/sources/point.md`).
5. Create a Pull Request: use [our PR naming conventions](https://docs.airbyte.com/contributing-to-airbyte/#pull-request-title-convention).
6. Pat yourself on the back for being an awesome contributor.
7. Someone from Airbyte will take a look at your PR and iterate with you to merge it into master.

## Configuration

The connector requires the following configuration parameters:

- `api_key` (required): Your Point API key for authentication
- `organization_id` (required): Your organization identifier  
- `distribution_type_id` (optional): Distribution type identifier (defaults to "1")

## API Details

The connector fetches data from the Point API endpoint:
- **Base URL**: `https://webservices.verzorgdeoverdracht.nl/api/DistributableData/`
- **Endpoint**: `GetLatest`
- **Method**: GET
- **Authentication**: API Key in header and query parameter
- **Response Format**: JSON with base64-encoded CSV data

The API returns a JSON response containing base64-encoded CSV data which is decoded and parsed into individual records.

## Supported Streams

- `point_data`: Main data stream containing CSV records with metadata

## Data Processing

1. **API Response**: Fetches JSON response from Point API
2. **Base64 Decoding**: Decodes the `Data` field containing CSV content
3. **CSV Parsing**: Parses semicolon-delimited CSV data
4. **Record Enrichment**: Adds API metadata to each CSV record
5. **Schema Validation**: Ensures records conform to defined schema

## Limitations

- Only supports full refresh sync mode
- CSV data must be semicolon-delimited
- No incremental sync support (API returns latest data only)
- Memory usage scales with CSV file size# Updated Sat Oct 18 19:28:13 CEST 2025
