FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if any
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY pyproject.toml .
# We need to install the package in editable mode or just install dependencies
# To keep it simple, we'll install clean
COPY src/ src/
COPY README.md .

RUN pip install --no-cache-dir .

EXPOSE 8000

ENTRYPOINT ["api-mocker"]
CMD ["start", "--host", "0.0.0.0", "--port", "8000"]
