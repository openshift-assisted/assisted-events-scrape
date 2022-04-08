#!/bin/bash -eu

cluster_domain=$(cat $KUBECONFIG | grep server | awk '{ print $2 }' | cut -d. -f2- | cut -d: -f1)
echo "elasticsearch-assisted-${OPENSHIFT_BUILD_NAMESPACE}.apps.${cluster_domain}"
