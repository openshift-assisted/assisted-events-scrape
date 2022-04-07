#!/bin/bash
image=$1
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

template_file=${SCRIPT_DIR}/../openshift/template.yaml

export IMAGE_NAME=$(echo $image | cut -d: -f1)
export IMAGE_TAG=$(echo $image | cut -d: -f2)
export IMAGE_PULL_POLICY=Never

# Get currently exported variables
current_envs=$(env | grep -f <(oc process --local=true -f openshift/template.yaml --parameters=true | tail -n+2 | awk '{ print $1 }') | tr '\n' ' ')

param=""
if [[ ! -z ${current_envs} ]]; then
   param="--param ${current_envs}"
fi
oc process --local=true -f openshift/template.yaml --output=yaml $param
