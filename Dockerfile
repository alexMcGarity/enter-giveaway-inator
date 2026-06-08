# Worker image for the cloud watch loop. Uses the official Playwright Python base,
# which ships Chromium and all its system libraries already matched to a Playwright
# version, so we do not have to apt-install browser deps ourselves.
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

# Install Python deps first for better layer caching.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

# Ensure a Chromium matching the installed Playwright is present.
RUN python -m playwright install chromium

COPY config.cloud.toml ./config.cloud.toml

ENV PYTHONUNBUFFERED=1
# seen.db is written to /data, which Fly mounts as a persistent volume.
CMD ["giveawayinator", "--watch", "15", "-c", "config.cloud.toml"]
