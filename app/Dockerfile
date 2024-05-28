# Build stage
FROM python:3.12.3-slim AS Build

# Install build dependencies
RUN apt-get update && apt-get install -y gcc && pip install cython

WORKDIR /app

COPY . .

# Run the bash script to convert py files into shared objects
RUN chmod +x converter.sh && ./converter.sh

# Runtime stage
FROM python:3.12.3-slim

WORKDIR /app

# Copy files
COPY . .

# Copy files from build stage
COPY --from=Build /app/shared_objects/*.so .

# Remove Python files that are now shared objects
RUN chmod +x cleanup.sh && ./cleanup.sh

# Install sqlite3
RUN apt-get update && apt-get install -y sqlite3 && apt-get autoclean

# Install python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Start gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "webpage:app"]