FROM python:3.11-slim

WORKDIR /app

# Install curl for healthchecks and poetry for package management
RUN apt-get update && apt-get install -y curl && \
    pip install poetry

# Copy poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Configure poetry to not use virtualenvs
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-root --only main

# Copy application code
COPY . .

# Expose the port the app runs on
EXPOSE 8002

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"] 