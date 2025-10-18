# Local Airbyte Deployment Guide for Point Connector

This guide provides step-by-step instructions to build and deploy the Point connector to your local Airbyte instance.

## Prerequisites

- Docker installed and running
- Local Airbyte instance running (docker-compose or Kubernetes)
- Access to Airbyte UI (typically http://localhost:8000 or http://localhost:8080)

## Step 1: Build the Docker Image

From the connector root directory (`source-point/`), build the Docker image:

```bash
# Build the Docker image with a specific tag
docker build -t airbyte/source-point:0.1.0 .

# Verify the image was built successfully
docker images | grep source-point
```

Expected output:
```
airbyte/source-point   0.1.0   <image_id>   <timestamp>   <size>
```

## Step 2: Test the Docker Image Locally

Before deploying to Airbyte, test the connector Docker image:

```bash
# Test the spec command
docker run --rm airbyte/source-point:0.1.0 spec

# Test the check command (requires config.json)
docker run --rm -v $(pwd)/secrets:/secrets airbyte/source-point:0.1.0 check --config /secrets/config.json

# Test the discover command
docker run --rm -v $(pwd)/secrets:/secrets airbyte/source-point:0.1.0 discover --config /secrets/config.json
```

## Step 3: Deploy to Local Airbyte (Docker Compose)

### Option A: For Docker Compose Airbyte Deployment

1. **Make the image available to Airbyte**:
   ```bash
   # The image is already available since it's built locally
   # No additional steps needed for docker-compose deployments
   ```

2. **Access Airbyte UI**:
   - Open your browser and go to `http://localhost:8000` (or your configured port)
   - Login to your Airbyte instance

3. **Add the Custom Connector**:
   - Navigate to **Settings** → **Sources**
   - Click **+ New connector**
   - Select **Add a new Docker connector**
   - Fill in the details:
     - **Connector display name**: `Point`
     - **Docker repository name**: `airbyte/source-point`
     - **Docker image tag**: `0.1.0`
     - **Connector documentation URL**: `https://webservices.verzorgdeoverdracht.nl/` (optional)
   - Click **Add**

## Step 4: Deploy to Local Airbyte (Kubernetes/Kind)

### Option B: For Kubernetes/Kind Airbyte Deployment

1. **Load the image into Kind cluster** (if using Kind):
   ```bash
   # Load the Docker image into the Kind cluster
   kind load docker-image airbyte/source-point:0.1.0 --name airbyte-abctl
   
   # Verify the image is loaded
   docker exec -it airbyte-abctl-control-plane crictl images | grep source-point
   ```

2. **Access Airbyte UI**:
   - Open your browser and go to `http://localhost:8080` (or your configured port)
   - Login to your Airbyte instance

3. **Add the Custom Connector**:
   - Navigate to **Settings** → **Sources**
   - Click **+ New connector**
   - Select **Add a new Docker connector**
   - Fill in the details:
     - **Connector display name**: `Point`
     - **Docker repository name**: `airbyte/source-point`
     - **Docker image tag**: `0.1.0`
     - **Connector documentation URL**: `https://webservices.verzorgdeoverdracht.nl/` (optional)
   - Click **Add**

## Step 5: Create a Source Connection

1. **Navigate to Sources**:
   - Go to **Sources** in the main navigation
   - Click **+ New source**

2. **Select Point Connector**:
   - Find and select **Point** from the connector list
   - Enter a name for your source (e.g., "Point Production Data")

3. **Configure the Connection**:
   - **API Key**: Enter your Point API key
   - **Organization ID**: Enter your organization identifier
   - **Distribution Type ID**: Enter the distribution type (defaults to "1")

4. **Test the Connection**:
   - Click **Test connection**
   - Verify that the connection is successful

5. **Save the Source**:
   - Click **Set up source** to save the configuration

## Step 6: Create a Sync Connection

1. **Create a Destination** (if not already done):
   - Go to **Destinations** and create a destination (e.g., Local JSON, PostgreSQL, etc.)

2. **Create a Connection**:
   - Go to **Connections**
   - Click **+ New connection**
   - Select your Point source and destination
   - Configure the sync:
     - **Sync frequency**: Choose your preferred frequency
     - **Destination Namespace**: Configure as needed
     - **Streams**: Enable the `point_data` stream
     - **Sync mode**: Full refresh (only mode currently supported)

3. **Run the Sync**:
   - Click **Set up connection**
   - Trigger a manual sync to test
   - Monitor the sync logs for any issues

## Troubleshooting

### Common Issues and Solutions

1. **Image not found error**:
   ```bash
   # Rebuild the image
   docker build -t airbyte/source-point:0.1.0 .
   
   # For Kind clusters, reload the image
   kind load docker-image airbyte/source-point:0.1.0 --name airbyte-abctl
   ```

2. **Connection test fails**:
   - Verify your API credentials are correct
   - Check that the API endpoint is accessible from your network
   - Review the connector logs in Airbyte UI

3. **Sync fails with encoding errors**:
   - This should be resolved with our automatic encoding detection
   - Check the logs for specific error messages

4. **No data synced**:
   - Verify the API returns data when called directly
   - Check the sync logs for parsing errors
   - Ensure the `point_data` stream is enabled in the connection

### Viewing Logs

1. **In Airbyte UI**:
   - Go to **Connections** → Select your connection
   - Click on a sync attempt to view detailed logs

2. **Docker logs** (for docker-compose):
   ```bash
   # View Airbyte worker logs
   docker logs airbyte-worker
   
   # View all Airbyte container logs
   docker-compose logs -f
   ```

3. **Kubernetes logs** (for K8s deployment):
   ```bash
   # View worker pod logs
   kubectl logs -l app=airbyte-worker -n airbyte
   
   # View specific job logs
   kubectl logs <job-name> -n airbyte
   ```

## Updating the Connector

To update the connector with new changes:

1. **Rebuild the image**:
   ```bash
   docker build -t airbyte/source-point:0.1.1 .
   ```

2. **For Kind clusters, reload**:
   ```bash
   kind load docker-image airbyte/source-point:0.1.1 --name airbyte-abctl
   ```

3. **Update in Airbyte UI**:
   - Go to **Settings** → **Sources**
   - Find your Point connector
   - Update the **Docker image tag** to `0.1.1`
   - Save the changes

4. **Update existing connections**:
   - Existing connections will automatically use the new version
   - You may need to refresh the schema if there are changes

## Production Considerations

### For Production Deployment:

1. **Push to Registry**:
   ```bash
   # Tag for your registry
   docker tag airbyte/source-point:0.1.0 your-registry.com/airbyte/source-point:0.1.0
   
   # Push to registry
   docker push your-registry.com/airbyte/source-point:0.1.0
   ```

2. **Use Registry Image**:
   - In Airbyte UI, use the full registry path: `your-registry.com/airbyte/source-point`

3. **Version Management**:
   - Use semantic versioning for tags
   - Keep track of changes in CHANGELOG.md
   - Test thoroughly before deploying to production

## Support

If you encounter issues:

1. Check the connector logs in Airbyte UI
2. Verify the standalone connector works: `python standalone_connector.py check --config secrets/config.json`
3. Review the troubleshooting section above
4. Check Docker image build logs for any errors

## Success Validation

Your deployment is successful when:

- ✅ Docker image builds without errors
- ✅ Connector appears in Airbyte UI source list
- ✅ Connection test passes
- ✅ Sync completes successfully
- ✅ Data appears in your destination
- ✅ Logs show successful processing of records (should see ~13,813 records)