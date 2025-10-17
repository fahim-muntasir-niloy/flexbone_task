FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY . .

# Specify the command to run on container startup.
# We use gunicorn for a production-ready server. Uvicorn is the worker class.
# The host 0.0.0.0 is necessary to accept connections from outside the container.
# The PORT environment variable is automatically set by Cloud Run.
CMD ["python", "main.py"]