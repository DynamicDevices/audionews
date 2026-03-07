#!/usr/bin/env bash
# Build and push the CI Docker image to Docker Hub (DynamicDevices org).
# Usage:
#   ./scripts/docker-build-push.sh [tag]
#   ./scripts/docker-build-push.sh        # builds and pushes :latest
#   ./scripts/docker-build-push.sh v1     # builds and pushes :v1
#
# Prereqs: docker login (or DOCKER_USERNAME/DOCKER_PASSWORD env for CI)

set -e
cd "$(dirname "$0")/.."
IMAGE="dynamicdevices/audionews-digest"
TAG="${1:-latest}"
echo "Building ${IMAGE}:${TAG} ..."
docker build -f docker/Dockerfile -t "${IMAGE}:${TAG}" .
echo "Pushing ${IMAGE}:${TAG} ..."
docker push "${IMAGE}:${TAG}"
echo "Done: ${IMAGE}:${TAG}"
