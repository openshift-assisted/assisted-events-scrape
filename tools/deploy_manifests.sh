#!/bin/bash -eu
platform=$1
image=$2
namespace=$3
log_level=DEBUG

ns="-n ${namespace}"
cli=kubectl
if [[ "${platform}" == "ocp" ]]; then
    cli=oc
fi

${cli} get ns ${namespace} || ${cli} create ns ${namespace}
# Deploy mockserver configmap
./tools/generate_mockserver_configmap.sh | ${cli} delete ${ns} -f - || true
./tools/generate_mockserver_configmap.sh | ${cli} create ${ns} -f - || true

# Deploy dependencies
${cli} apply ${ns} -f assisted-events-scrape/tests/integration/manifests

if [[ "${platform}" == "ocp" ]]; then
    ${cli} process --local=true -f assisted-events-scrape/tests/integration/ci-manifests/ --output=yaml --param ELASTICSEARCH_ROUTE_HOST=$(./tools/get_ocp_route_host.sh elasticsearch-assisted) MINIO_ROUTE_HOST=$(./tools/get_ocp_route_host.sh minio-assisted) | ${cli} apply ${ns} -f -
fi

${cli} wait ${ns} --timeout=120s --for=condition=Available deployment --all
${cli} wait ${ns} --timeout=300s --for=condition=Ready pods -l app=elasticsearch-master
${cli} wait ${ns} --timeout=300s --for=condition=Ready pods -l app=mockserver
${cli} wait ${ns} --timeout=300s --for=condition=Ready pods -l app=minio

# Write elasticsearch index templates
if [[ "${platform}" == "ocp" ]]; then
    es_host=$(./tools/get_ocp_route_host.sh elasticsearch-assisted):80
else
    es_host=$(./tools/get_endpoint.sh ${namespace} elasticsearch-master)
fi

./tools/create_elastic_templates.sh ${es_host}

# Deploy assisted-events-scraper
if [[ "${platform}" == "ocp" ]]; then
    image_name=$(echo $ASSISTED_EVENTS_SCRAPE_IMAGE | cut -d: -f1)
    image_tag=$(echo $ASSISTED_EVENTS_SCRAPE_IMAGE | cut -d: -f2)
    ${cli} process --output=yaml ${ns} -f openshift/template.yaml --param IMAGE_NAME=${image_name} IMAGE_TAG=${image_tag} LOGLEVEL=${log_level} | ${cli} apply ${ns} -f -
else
    ./tools/ocp2k8s.sh ${image} | ${cli} apply ${ns} -f -
fi

${cli} wait ${ns} --timeout=30s --for=condition=Available deployment --all
${cli} wait ${ns} --timeout=30s --for=condition=Ready pods -l app=assisted-events-scrape

${cli} ${ns} create job test-s3 --from=cronjob/ccx-export
${cli} wait ${ns} --timeout=30s --for=condition=complete job test-s3
${cli} delete ${ns} job test-s3
