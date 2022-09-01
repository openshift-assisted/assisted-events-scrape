#!/usr/bin/env python3
"""
This script generates config for mockserver (https://www.mock-server.com/)
It will look for fixtures in the integration test folder, and build the JSON configuration
needed by mockserver.
"""
import json
import logging
from pathlib import Path


def get_rule(path: str, body: str, queryStringParameters=None) -> dict:
    rule = {
        "httpRequest": {
            "path": path,
        },
        "httpResponse": {
            "headers": {
                "Content-Type": ["application/json"]
            },
            "body": body
        }
    }
    if queryStringParameters:
        rule["httpRequest"]["queryStringParameters"] = queryStringParameters
    return rule


def get_items(glob_pattern: str):
    items = []
    for filename in fixtures_path.glob(glob_pattern):
        with open(filename, "r") as f:
            item = json.load(f)
            items.append(item)
    return items


fixtures_path = Path(__file__).parent.joinpath('../assisted-events-scrape/tests/integration/fixtures/')

clusters = get_items('clusters-*')
infra_envs = get_items('infra_envs-*')

individual_infra_envs = get_items('infra_env-*')

clusters_txt = json.dumps(clusters)
infra_envs_txt = json.dumps(infra_envs)
rules = []
rules.append(get_rule(
    path="/api/assisted-install/v2/component-versions",
    body="{\"release_tag\":\"v2.1.4\",\"versions\":{\"assisted-installer\":\"registry.redhat.io/rhai-tech-preview/assisted-installer-rhel8:v1.0.0-125\",\"assisted-installer-controller\":\"registry.redhat.io/rhai-tech-preview/assisted-installer-reporter-rhel8:v1.0.0-162\",\"assisted-installer-service\":\"quay.io/app-sre/assisted-service:61d0164\",\"discovery-agent\":\"registry.redhat.io/rhai-tech-preview/assisted-installer-agent-rhel8:v1.0.0-89\"}}"  # noqa: E501
))
rules.append(get_rule(
    path="/api/assisted-install/v2/clusters",
    body=clusters_txt
))
rules.append(get_rule(
    path="/api/assisted-install/v2/infra-envs",
    body=infra_envs_txt
))

for infra_env in individual_infra_envs:
    infra_env_id = infra_env["id"]
    rule = get_rule(
        path=f"/api/assisted-install/v2/infra-envs/{infra_env_id}",
        body=infra_env
    )
    rules.append(rule)

for cluster in clusters:
    cluster_id = cluster["id"]
    event_file_path = fixtures_path / f"events-{cluster_id}.json"
    try:
        with event_file_path.open("r") as f:
            events_txt = json.load(f)
            params = {"cluster_id": [cluster_id]}
            rule = get_rule(
                path="/api/assisted-install/v2/events",
                queryStringParameters=params,
                body=events_txt)
            rules.append(rule)
    except IOError:
        logging.warning(f"File {event_file_path} not found")

    try:
        cluster_file_path = fixtures_path / f"cluster-{cluster_id}.json"
        with cluster_file_path.open("r") as f:
            cluster_txt = json.load(f)
            rule = get_rule(
                path=f"/api/assisted-install/v2/clusters/{cluster_id}",
                body=cluster_txt)
            rules.append(rule)
    except IOError:
        logging.warning(f"File {event_file_path} not found")

print(json.dumps(rules))
