#!/bin/bash
image=$1
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Get currently exported variables
current_envs=$(env | grep -f <(cat ${SCRIPT_DIR}/../openshift/template.yaml | yq --raw-output '.parameters[] | "\(.name)"'))

# Extract variables from parameters
eval $(cat ${SCRIPT_DIR}/../openshift/template.yaml | yq --raw-output '.parameters[] | "export \(.name)=\"\(.value)\""')

# Override parameters env var with current env vars
exportable_vars=$(echo ${current_envs} | sed 's/^/export /g')
if [[ ! -z "${current_envs// }" ]]; then
    eval "${exportable_vars}"
fi

export IMAGE_NAME=$(echo $image | cut -d: -f1)
export IMAGE_TAG=$(echo $image | cut -d: -f2)

# Substitute variables named in parameters
envs=$(cat ${SCRIPT_DIR}/../openshift/template.yaml | yq --raw-output '.parameters[] | "${\(.name)}"' | tr '\n' ' ')

cat ${SCRIPT_DIR}/../openshift/template.yaml | sed 's/{{/{/g' | sed 's/}}/}/g' | envsubst "${envs}" | yq -y '.objects[]' | sed 's/imagePullPolicy: Always/imagePullPolicy: Never/g'
