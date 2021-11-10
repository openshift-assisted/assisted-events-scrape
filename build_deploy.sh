#!/bin/bash

set -exu

TAG=$(git rev-parse --short=7 HEAD)
REPO="quay.io/app-sre/assisted-events-scrape"
export ASSISTED_EVENTS_SCRAPE_IMAGE="${REPO}:${TAG}"
make build-image
docker login -u="${QUAY_USER}" -p="${QUAY_TOKEN}" quay.io
docker tag "${ASSISTED_EVENTS_SCRAPE_IMAGE}" "${REPO}:latest"
docker push "${ASSISTED_EVENTS_SCRAPE_IMAGE}"
docker push "${REPO}:latest"
