# Worker image for the cloud watch loop.
# We base on python:3.12-slim (the package needs Python 3.11+ for tomllib) and let
# Playwright pull Chromium plus its system libraries via `install --with-deps`. This
# keeps the Python version and the Playwright browser exactly matched to our pip pin.
FROM python:3.12-slim

WORKDIR /app

# Install Python deps first for better layer caching.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

# Chromium + all required OS libraries, matched to the installed Playwright version.
RUN playwright install --with-deps chromium

COPY config.cloud.toml ./config.cloud.toml

ENV PYTHONUNBUFFERED=1
# seen.db is written to /data, which Fly mounts as a persistent volume.
CMD ["giveawayinator", "--at", "10:00,17:00", "--tz", "America/Chicago", "-c", "config.cloud.toml"]
