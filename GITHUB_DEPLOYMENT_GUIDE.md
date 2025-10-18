# GitHub Container Registry Deployment Guide

This guide explains how to deploy the Point connector using GitHub Container Registry (GHCR) for easy integration with your Airbyte instance.

## Overview

The connector is automatically built and published to GitHub Container Registry using GitHub Actions. This allows you to pull the Docker image directly from GitHub into your Airbyte deployment.

## Prerequisites

- GitHub account
- Git installed locally
- Docker installed locally (for testing)
- Access to your Airbyte instance

## Step 1: Set Up GitHub Repository

### 1.1 Create GitHub Repository

1. Go to [GitHub](https://github.com) and create a new repository
2. Name it something like `airbyte-source-point` or `source-point-connector`
3. Make it **public** (required for GHCR access without authentication)
4. Initialize with README if desired

### 1.2 Clone and Push Code

```bash
# Clone your new repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME

# Copy all connector files to the repository
# (Copy all files from your current source-point directory)

# Add all files
git add .

# Commit
git commit -m "Initial commit: Point API connector"

# Push to GitHub
git push origin main
```

## Step 2: Automatic Docker Image Building

### 2.1 GitHub Actions Workflow

The repository includes a GitHub Actions workflow (`.github/workflows/build-and-push.yml`) that automatically:

- ✅ Builds the Docker image on every push to main/master
- ✅ Pushes to GitHub Container Registry (ghcr.io)
- ✅ Creates tags for versions and latest
- ✅ Tests the built image
- ✅ Supports both AMD64 and ARM64 architectures

### 2.2 Triggering the Build

The workflow triggers automatically when you:
- Push to `main` or `master` branch
- Create a new tag (e.g., `v0.1.0`)
- Create a pull request

### 2.3 Monitoring the Build

1. Go to your GitHub repository
2. Click on the **Actions** tab
3. You'll see the "Build and Push Docker Image" workflow running
4. Click on a workflow run to see detailed logs

## Step 3: Using the Docker Image in Airbyte

### 3.1 Image Location

Once built, your Docker image will be available at:
```
ghcr.io/YOUR_USERNAME/YOUR_REPO_NAME:latest
```

For example:
```
ghcr.io/johndoe/airbyte-source-point:latest
```

### 3.2 Adding to Airbyte (Docker Compose)

1. **Access Airbyte UI**: Go to `http://localhost:8000` (or your Airbyte URL)

2. **Navigate to Sources**: 
   - Go to **Settings** → **Sources**
   - Click **+ New connector**
   - Select **Add a new Docker connector**

3. **Configure the Connector**:
   - **Connector display name**: `Point`
   - **Docker repository name**: `ghcr.io/YOUR_USERNAME/YOUR_REPO_NAME`
   - **Docker image tag**: `latest` (or specific version like `v0.1.0`)
   - **Connector documentation URL**: `https://webservices.verzorgdeoverdracht.nl/` (optional)

4. **Save**: Click **Add** to save the connector

### 3.3 Adding to Airbyte (Kubernetes/Kind)

For Kubernetes deployments, you may need to pull the image first:

```bash
# Pull the image
docker pull ghcr.io/YOUR_USERNAME/YOUR_REPO_NAME:latest

# For Kind clusters, load the image
kind load docker-image ghcr.io/YOUR_USERNAME/YOUR_REPO_NAME:latest --name airbyte-abctl
```

Then follow the same UI steps as above.

## Step 4: Creating a Source Connection

1. **Navigate to Sources**: Go to **Sources** in the main navigation
2. **Create New Source**: Click **+ New source**
3. **Select Point Connector**: Find and select **Point** from the connector list
4. **Configure Connection**:
   - **Source name**: Enter a name (e.g., "Point Production Data")
   - **API Key**: Enter your Point API key
   - **Organization ID**: Enter your organization identifier
   - **Distribution Type ID**: Enter the distribution type (defaults to "1")
5. **Test Connection**: Click **Test connection** to verify
6. **Save**: Click **Set up source** to save

## Step 5: Version Management

### 5.1 Creating Releases

To create versioned releases:

```bash
# Tag a new version
git tag v0.1.0
git push origin v0.1.0
```

This will trigger the GitHub Action to build and push with the version tag.

### 5.2 Using Specific Versions

In Airbyte, you can specify exact versions:
- **Docker image tag**: `v0.1.0` (instead of `latest`)

### 5.3 Updating the Connector

To update the connector:

1. Make changes to your code
2. Commit and push to GitHub
3. The new image will be automatically built
4. In Airbyte UI:
   - Go to **Settings** → **Sources**
   - Find your Point connector
   - Update the **Docker image tag** if needed
   - Save changes

## Step 6: Troubleshooting

### 6.1 Build Failures

If the GitHub Action fails:

1. Check the **Actions** tab in your GitHub repository
2. Click on the failed workflow run
3. Expand the failed step to see error details
4. Common issues:
   - Dockerfile syntax errors
   - Missing dependencies in pyproject.toml
   - Test failures

### 6.2 Image Pull Failures

If Airbyte can't pull the image:

1. **Verify Image Exists**: Check GitHub Packages tab in your repository
2. **Check Image Name**: Ensure the repository name matches exactly
3. **Public Repository**: Ensure your repository is public for GHCR access
4. **Network Access**: Ensure your Airbyte instance can access GitHub

### 6.3 Connector Not Working

If the connector fails in Airbyte:

1. **Check Logs**: View sync logs in Airbyte UI
2. **Test Locally**: Test the Docker image locally:
   ```bash
   docker run --rm ghcr.io/YOUR_USERNAME/YOUR_REPO_NAME:latest spec
   ```
3. **Verify Configuration**: Ensure API credentials are correct

## Step 7: Advanced Configuration

### 7.1 Private Repositories

If you need to use a private repository:

1. Create a GitHub Personal Access Token with `read:packages` permission
2. In your Airbyte deployment, configure Docker to authenticate with GHCR
3. Use the token for authentication

### 7.2 Custom Build Triggers

You can modify `.github/workflows/build-and-push.yml` to:
- Build only on specific branches
- Add additional testing steps
- Deploy to multiple registries
- Add security scanning

### 7.3 Multi-Architecture Support

The workflow builds for both AMD64 and ARM64 architectures, ensuring compatibility with:
- Intel/AMD processors (x86_64)
- Apple Silicon (M1/M2) and ARM servers

## Example Repository Structure

```
your-repo/
├── .github/
│   └── workflows/
│       └── build-and-push.yml          # GitHub Actions workflow
├── source_point/                       # Connector source code
├── unit_tests/                         # Unit tests
├── integration_tests/                  # Integration tests
├── docs/                              # Documentation
├── Dockerfile                         # Docker configuration
├── pyproject.toml                     # Python dependencies
├── metadata.yaml                      # Airbyte metadata
├── README.md                          # Project documentation
├── GITHUB_DEPLOYMENT_GUIDE.md         # This guide
└── LOCAL_DEPLOYMENT_GUIDE.md          # Local deployment guide
```

## Security Best Practices

1. **Environment Variables**: Store sensitive data in GitHub Secrets
2. **Public Images**: Only use public repositories for non-sensitive connectors
3. **Version Pinning**: Use specific version tags in production
4. **Regular Updates**: Keep dependencies updated for security patches

## Support

If you encounter issues:

1. Check the GitHub Actions logs for build errors
2. Verify your Airbyte deployment can access GitHub Container Registry
3. Test the Docker image locally before deploying
4. Ensure your API credentials are valid and have proper permissions

## Quick Reference

### Image URL Format
```
ghcr.io/USERNAME/REPOSITORY:TAG
```

### Common Tags
- `latest` - Latest build from main branch
- `v0.1.0` - Specific version tag
- `main` - Latest build from main branch

### Testing Commands
```bash
# Test locally
docker run --rm ghcr.io/USERNAME/REPO:latest spec

# Pull latest
docker pull ghcr.io/USERNAME/REPO:latest

# Load into Kind
kind load docker-image ghcr.io/USERNAME/REPO:latest --name airbyte-abctl
```

This setup provides a professional, automated deployment pipeline for your Point connector that integrates seamlessly with Airbyte!