# CI Docker image (audionews-digest)

Image used by GitHub Actions for the daily news digest workflow. Includes Python 3.11, ffmpeg, git, git-lfs, and pip dependencies from `requirements.txt`.

## Build locally

From the **repo root**:

```bash
docker build -f docker/Dockerfile -t dynamicdevices/audionews-digest:latest .
```

## Push to Docker Hub (DynamicDevices org)

1. Log in: `docker login` (use your Docker Hub credentials; org push requires org membership or automated build).
2. From repo root:

```bash
./scripts/docker-build-push.sh           # push :latest
./scripts/docker-build-push.sh v1        # push :v1
```

Image: **`dynamicdevices/audionews-digest`**  
Tags: `latest` (default), or pass a tag as the first argument.

## Use in CI

The workflow uses `container: dynamicdevices/audionews-digest:latest` for the jobs that need Python + ffmpeg. **Push the image at least once** before relying on CI (e.g. run `./scripts/docker-build-push.sh` from repo root after `docker login`). After pushing a new image, re-run the workflow or wait for the next scheduled run.
