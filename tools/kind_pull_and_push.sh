#!/bin/bash
for image in $(cat assisted-events-scrape/tests/integration/manifests/* | grep 'image:' | cut -d':' -f2,3 | tr -d ' "' | sort | uniq); do
    docker pull "${image}"
    kind load docker-image --name assisted-events-scrape "${image}"
done
for image in $(oc process --local=true -f openshift/template.yaml --param IMAGE_TAG=foobar | grep '"image":' | grep -v assisted-events-scrape | tr -d ' ",' | cut -d: -f2,3); do
    docker pull "${image}"
    kind load docker-image --name assisted-events-scrape "${image}"
done

