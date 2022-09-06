import json

_ATTRIBUTES_TO_SUMMARIZE = {
    "infra_env": ["type", "cpu_architecture", "openshift_version"]
}


def reshape_host(host):
    if "inventory" in host:
        host["host_inventory"] = json.loads(host["inventory"])
        del host["inventory"]


def get_hosts_summary(hosts):
    # get automatic summary
    summary = _get_summary(_ATTRIBUTES_TO_SUMMARIZE, hosts)
    # get manual summary
    summary["host_count"] = len(hosts)
    summary["heterogeneous_arch"] = _is_heterogeneous(summary)
    summary["iso_type"] = _get_summarized_iso_type(summary)
    return summary


def _get_summarized_iso_type(summary):
    if "infra_env" not in summary or "type" not in summary["infra_env"]:
        return "Unknown"
    for iso_type, ratio in summary["infra_env"]["type"].items():
        if ratio >= 1:
            return iso_type
    return "mixed"


def _is_heterogeneous(summary):
    if "infra_env" not in summary or "cpu_architecture" not in summary["infra_env"]:
        return False
    # If any arch has 1.0 ratio, it means all hosts belong to such arch
    for ratio in summary["infra_env"]["cpu_architecture"].values():
        if ratio == 1:
            return False
    return True


def _get_summary(to_summarize, hosts):
    summary = {}
    # Get count summary
    for root, labels in to_summarize.items():
        summary[root] = {}
        for label in labels:
            for host in hosts:
                if root in host and label in host[root]:
                    if label not in summary[root]:
                        summary[root][label] = {}
                    value = host[root][label]
                    if value in summary[root][label]:
                        summary[root][label][value] += 1
                    else:
                        summary[root][label][value] = 1
    _get_relative_summary(summary)
    return summary


def _get_relative_summary(summary):
    for secondary_summary in summary.values():
        for label in secondary_summary:
            total = 0
            for k, v in secondary_summary[label].items():
                total += v
            for k, v in secondary_summary[label].items():
                if total == 0:
                    secondary_summary[label][k] = 0
                else:
                    secondary_summary[label][k] = v / total
