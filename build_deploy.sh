#!/bin/bash

set -exu

TAG=$(git rev-parse --short=7 HEAD)
REPO="quay.io/app-sre/assisted-events-scrape"
ASSISTED_EVENTS_SCRAPE_IMAGE="${REPO}:${TAG}"
make build-image
docker login -u="${QUAY_USER}" -p="${QUAY_TOKEN}" quay.io
docker tag "${IMAGE}" "${REPO}:latest"
docker push "${IMAGE}"
docker push "${REPO}:latest"
