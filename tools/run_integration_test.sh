#!/bin/bash

namespace=$1
platform=$2


if [[ "${platform}" == "ocp" ]]; then
    export ES_SERVER=$(./tools/get_ocp_route_host.sh elasticsearch-assisted):80
    export AWS_S3_ENDPOINT="http://"$(./tools/get_ocp_route_host.sh minio-assisted):80
else
    export ES_SERVER=$(./tools/get_endpoint.sh ${namespace} elasticsearch-master)
    export AWS_S3_ENDPOINT=http://$(./tools/get_endpoint.sh ${namespace} ai-events-minio)
fi

export ES_INDEX=assisted-service-events
export AWS_SECRET_ACCESS_KEY=$(oc -n ${namespace} get secret ai-ccx-integration -o jsonpath='{.data.aws_secret_access_key}' | base64 --decode)
export AWS_ACCESS_KEY_ID=$(oc -n ${namespace} get secret ai-ccx-integration -o jsonpath='{.data.aws_access_key_id}' | base64 --decode)
export AWS_S3_BUCKET=$(oc -n ${namespace} get secret ai-ccx-integration -o jsonpath='{.data.bucket}' | base64 --decode)

pytest assisted-events-scrape/tests/integration
