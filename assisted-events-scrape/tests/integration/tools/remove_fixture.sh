#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

fixtures_dir=${SCRIPT_DIR}/../assisted-events-scrape/tests/integration/fixtures/

cluster_id=$1

rm -f "${fixtures_dir}/clusters-${cluster_id}.json"
rm -f "${fixtures_dir}/events-${cluster_id}.json"
rm -f "${fixtures_dir}/cluster-${cluster_id}.json"