#!/bin/bash

set -exu

TAG=$(git rev-parse --short=7 HEAD)
REPO="quay.io/app-sre/assisted-events-scrape"
export ASSISTED_EVENTS_SCRAPE_IMAGE="${REPO}:${TAG}"
export CONTAINER_BUILD_EXTRA_PARAMS="--no-cache"
export ELASTICDUMP_IMAGE="quay.io/app-sre/elasticdump:v6.82.3"

make build-image
make build-elasticdump-image

DOCKER_CONF="$PWD/assisted/.docker"
mkdir -p "$DOCKER_CONF"
docker --config="$DOCKER_CONF" login -u="${QUAY_USER}" -p="${QUAY_TOKEN}" quay.io
docker tag "${ASSISTED_EVENTS_SCRAPE_IMAGE}" "${REPO}:latest"
docker --config="$DOCKER_CONF" push "${ASSISTED_EVENTS_SCRAPE_IMAGE}"
docker --config="$DOCKER_CONF" push "${REPO}:latest"
docker --config="$DOCKER_CONF" push "${ELASTICDUMP_IMAGE}"
