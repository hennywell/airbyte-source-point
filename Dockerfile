FROM airbyte/python-connector-base:1.2.0

# Copy the connector source code
COPY . /airbyte/integration_code

# Install the connector package
WORKDIR /airbyte/integration_code
RUN pip install .

# Set the entrypoint
ENV AIRBYTE_ENTRYPOINT "python /airbyte/integration_code/source_point/run.py"
ENTRYPOINT ["python", "/airbyte/integration_code/source_point/run.py"]

# Labels for metadata
LABEL io.airbyte.version=0.1.4
LABEL io.airbyte.name=ghcr.io/hennywell/airbyte-source-point