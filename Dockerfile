FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY . .

# Expose port (Cloud Run or Docker will use this)
EXPOSE 6969

# Start the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "6969"]