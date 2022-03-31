#!/usr/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

fixtures_dir=${SCRIPT_DIR}/../assisted-events-scrape/tests/integration/fixtures/

cluster_id=$1

token=$(curl -sS -XPOST https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token -d "client_id=cloud-services&grant_type=refresh_token&refresh_token=$OFFLINE_TOKEN" | jq -r ".access_token")

curl -sS -H "Authorization: bearer $token"  https://api.stage.openshift.com/api/assisted-install/v2/clusters | jq -crM '.[] | select(.id=="'${cluster_id}'")' > "${fixtures_dir}/clusters-${cluster_id}.json"

curl -sS -H "Authorization: bearer $token"  https://api.stage.openshift.com/api/assisted-install/v2/clusters/$cluster_id > "${fixtures_dir}/cluster-${cluster_id}.json"

curl -sS -H "Authorization: bearer $token"  "https://api.stage.openshift.com/api/assisted-install/v2/events?cluster_id=${cluster_id}" > "${fixtures_dir}/events-${cluster_id}.json"
