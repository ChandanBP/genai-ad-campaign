# Use a slim Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy only the files needed
COPY . .

# Install dependencies
RUN pip install --upgrade pip \
  && pip install google-adk fastapi uvicorn moviepy

# Expose port 8080 (required by Cloud Run)
EXPOSE 8080

# Entrypoint
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
