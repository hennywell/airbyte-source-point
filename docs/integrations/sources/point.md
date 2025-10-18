# Point

<HideInUI>

This page contains the setup guide and reference information for the [Point](https://webservices.verzorgdeoverdracht.nl/) source connector.

</HideInUI>

## Prerequisites

To set up the Point source connector, you'll need:

- A Point API account with access to the DistributableData API
- Your API key for authentication
- Your organization ID
- Access to the Point web services API endpoint

**Security Note**: The connector uses header-only authentication for enhanced security. The API key is sent only in the request header, not in query parameters.

## Setup guide

### Step 1: Obtain your API credentials

1. Log into your Point account
2. Navigate to the API settings or contact your Point administrator
3. Generate or obtain your API key
4. Note your organization ID

### Step 2: Set up the Point connector in Airbyte

#### For Airbyte Cloud:

1. [Log into your Airbyte Cloud](https://cloud.airbyte.com/workspaces) account.
2. Click Sources and then click + New source.
3. On the Set up the source page, select Point from the Source type dropdown.
4. Enter a name for the Point connector.
5. For **API Key**, enter your Point API key.
6. For **Organization ID**, enter your organization identifier.
7. (Optional) For **Distribution Type ID**, enter the distribution type (defaults to "1").
8. Click **Set up source**.

#### For Airbyte Open Source:

1. Navigate to the Airbyte Open Source dashboard.
2. Click Sources and then click + New source.
3. On the Set up the source page, select Point from the Source type dropdown.
4. Enter a name for the Point connector.
5. For **API Key**, enter your Point API key.
6. For **Organization ID**, enter your organization identifier.
7. (Optional) For **Distribution Type ID**, enter the distribution type (defaults to "1").
8. Click **Set up source**.

## Supported sync modes

The Point source connector supports the following [sync modes](https://docs.airbyte.com/cloud/core-concepts/#connection-sync-modes):

| Feature                       | Supported? |
| :---------------------------- | :--------- |
| Full Refresh Sync             | Yes        |
| Incremental Sync              | No         |
| Replicate Incremental Deletes | No         |
| SSL connection                | Yes        |
| Namespaces                    | No         |

## Supported Streams

The Point connector supports the following stream:

- **point_data**: Contains the CSV data from the Point API with metadata

### point_data

This stream fetches the latest distributable data from the Point API. The API returns base64-encoded CSV data which is decoded and parsed into individual records.

Each record contains:
- `row_index`: The index of the row in the CSV data
- `metadata`: Information about the API response including identifier, filename, timestamp, etc.
- `data`: The actual CSV row data as key-value pairs

## Performance considerations

- The connector fetches all available data in each sync (full refresh only)
- Memory usage scales with the size of the CSV data returned by the API
- Large CSV files may require more memory and processing time
- The API endpoint returns the latest data snapshot

## Data type map

| Integration Type | Airbyte Type |
| :--------------- | :----------- |
| `string`         | `string`     |
| `integer`        | `integer`    |
| `object`         | `object`     |

## Limitations & Troubleshooting

### Limitations

- **Full refresh only**: The connector only supports full refresh sync mode as the API returns the latest data snapshot
- **CSV format dependency**: The API must return semicolon-delimited CSV data
- **Memory constraints**: Large CSV files may cause memory issues
- **Single endpoint**: Only supports the GetLatest endpoint

### Troubleshooting

#### Connection issues

If you encounter connection issues:

1. Verify your API key is correct and active
2. Ensure your organization ID is valid
3. Check that you have access to the Point API
4. Verify the API endpoint is accessible from your network

#### Data parsing issues

If data parsing fails:

1. Check that the API returns valid base64-encoded data
2. Verify the CSV format uses semicolon delimiters
3. Ensure the CSV data is properly formatted

#### Performance issues

If syncs are slow or fail:

1. Monitor memory usage during syncs
2. Consider the size of the CSV data being processed
3. Check network connectivity and API response times

#### Common error messages

- **"Missing required configuration field"**: Ensure all required fields (API key, organization ID) are provided
- **"Failed to connect to Point API"**: Check your credentials and network connectivity
- **"Failed to decode base64 data"**: The API response may not contain valid base64-encoded data
- **"Error parsing response"**: The API response format may be unexpected

## Changelog

<details>
  <summary>Expand to review</summary>

| Version | Date       | Pull Request | Subject                                     |
| :------ | :--------- | :----------- | :------------------------------------------ |
| 0.1.0   | 2024-01-01 | [#XXXXX](https://github.com/airbytehq/airbyte/pull/XXXXX) | Initial release of Point source connector |

</details>