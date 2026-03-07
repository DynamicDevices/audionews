# CI image for AudioNews daily digest: Python 3.11, ffmpeg, git-lfs, pip deps.
# Build from repo root: docker build -f docker/Dockerfile -t dynamicdevices/audionews-digest:latest .
# Push: docker push dynamicdevices/audionews-digest:latest

FROM python:3.11-slim-bookworm

RUN apt-get update -qq && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    git-lfs \
    && rm -rf /var/lib/apt/lists/* \
    && git lfs install

WORKDIR /workspace

# Install Python dependencies (copied from repo so image is reproducible)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Default command for local use; CI overrides with checkout + script
CMD ["python", "--version"]
