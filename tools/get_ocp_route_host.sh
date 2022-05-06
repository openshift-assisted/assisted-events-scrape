#!/bin/bash -eu

prefix=$1
cluster_domain=$(cat $KUBECONFIG | grep server | awk '{ print $2 }' | cut -d. -f2- | cut -d: -f1)
echo "${prefix}-${OPENSHIFT_BUILD_NAMESPACE}.apps.${cluster_domain}"
