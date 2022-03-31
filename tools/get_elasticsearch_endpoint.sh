#!/bin/bash -e
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

source "${SCRIPT_DIR}/utils.sh"

container_id=$(docker ps | grep kindest | awk '{ print $1}')
if [ -z "${container_id}" ]; then
    echo "Could not find container ID for kind"
    exit 1;
fi
port=$(kubectl get svc elasticsearch-master -o jsonpath='{.spec.ports[0].nodePort}')
if [ -z "${port}" ]; then
    echo "Could not find nodePort for elasticsearch svc. Is it NodePort type?"
    exit 1;
fi

ip=$($(get_container_runtime_command) inspect $container_id | jq -r '.[0].NetworkSettings.Networks.kind.IPAddress')
if [ -z "${ip}" ]; then
    echo "Could not find IP address for kind. Something went wrong"
    exit 1;
fi

echo "${ip}:${port}"
