#!/bin/bash

set -exu

TAG=$(git rev-parse --short=7 HEAD)
REPO="quay.io/app-sre/assisted-events-scrape"
export ASSISTED_EVENTS_SCRAPE_IMAGE="${REPO}:${TAG}"
export CONTAINER_BUILD_EXTRA_PARAMS="--no-cache"
make build-image

export ELASTICDUMP_IMAGE_REPO="quay.io/app-sre/elasticdump"
export ELASTICDUMP_IMAGE_TAG="v6.82.3"
export ELASTICDUMP_ORIGINAL_REPO="elasticdump/elasticsearch-dump"

DOCKER_CONF="$PWD/assisted/.docker"
mkdir -p "$DOCKER_CONF"
docker --config="$DOCKER_CONF" login -u="${QUAY_USER}" -p="${QUAY_TOKEN}" quay.io
docker tag "${ASSISTED_EVENTS_SCRAPE_IMAGE}" "${REPO}:latest"
docker --config="$DOCKER_CONF" push "${ASSISTED_EVENTS_SCRAPE_IMAGE}"
docker --config="$DOCKER_CONF" push "${REPO}:latest"
docker tag "${ELASTICDUMP_ORIGINAL_REPO}:${ELASTICDUMP_IMAGE_TAG}" "${ELASTICDUMP_IMAGE_REPO}:${ELASTICDUMP_IMAGE_TAG}"
docker --config="$DOCKER_CONF" push "${ELASTICDUMP_IMAGE_REPO}:${ELASTICDUMP_IMAGE_TAG}"
