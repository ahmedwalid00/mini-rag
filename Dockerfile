# Use an official Python runtime as a parent image
FROM python:3.10-slim 

# Set environment variables to prevent Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies if needed (example)
# RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY src/requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
# Make sure this Dockerfile is in the root, so '.' copies everything from the root
COPY src/ . 

# Make port 8000 available to the world outside this container
EXPOSE 8000 

# Define environment variable (can be overridden by docker-compose)
# ENV NAME World

# Run the application when the container launches (example for FastAPI with Uvicorn)
# Adjust this command based on how you run your specific app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 