from process import get_hosts_summary


class TestHostProcess:
    def test_get_hosts_summary(self):
        hosts = [
            {
                "id": "foo",
                "infra_env_id": "12345",
                "infra_env": {
                    "type": "minimal-iso"
                }
            },
            {
                "id": "bar",
                "infra_env_id": "12345",
                "infra_env": {
                    "type": "minimal-iso"
                }
            },
        ]
        summary = get_hosts_summary(hosts)
        assert "host_count" in summary
        assert 2 == summary["host_count"]
        assert "infra_env" in summary
        assert "type" in summary["infra_env"]
        assert "minimal-iso" in summary["infra_env"]["type"]
        assert summary["infra_env"]["type"]["minimal-iso"] == 1
        assert "minimal-iso" == summary["iso_type"]

        assert_is_not_multiarch(summary)

    def test_get_hosts_summary_multiarch(self):
        hosts = [
            {
                "id": "foo",
                "infra_env_id": "12345",
                "infra_env": {
                    "type": "minimal-iso",
                    "cpu_architecture": "x86",
                },
            },
            {
                "id": "bar",
                "infra_env_id": "12345",
                "infra_env": {
                    "type": "minimal-iso",
                    "cpu_architecture": "x86",
                },
            },
            {
                "id": "qux",
                "infra_env_id": "12345",
                "infra_env": {
                    "type": "minimal-iso",
                    "cpu_architecture": "arm64",
                },
            },
        ]
        summary = get_hosts_summary(hosts)
        assert "host_count" in summary
        assert 3 == summary["host_count"]

        assert "infra_env" in summary
        assert "type" in summary["infra_env"]
        assert "minimal-iso" in summary["infra_env"]["type"]
        assert summary["infra_env"]["type"]["minimal-iso"] == 1

        assert "cpu_architecture" in summary["infra_env"]
        assert "x86" in summary["infra_env"]["cpu_architecture"]
        assert summary["infra_env"]["cpu_architecture"]["x86"] < 1

        assert "cpu_architecture" in summary["infra_env"]
        assert "arm64" in summary["infra_env"]["cpu_architecture"]
        assert summary["infra_env"]["cpu_architecture"]["arm64"] < 1
        assert "minimal-iso" == summary["iso_type"]

        assert_is_multiarch(summary)

    def test_get_hosts_summary_not_multiarch(self):
        hosts = [
            {
                "id": "foo",
                "infra_env_id": "12345",
                "infra_env": {
                    "type": "minimal-iso",
                    "cpu_architecture": "x86",
                },
            },
            {
                "id": "bar",
                "infra_env_id": "12345",
                "infra_env": {
                    "type": "minimal-iso",
                    "cpu_architecture": "x86",
                },
            },
            {
                "id": "qux",
                "infra_env_id": "12345",
                "infra_env": {
                    "type": "full-iso",
                    "cpu_architecture": "x86",
                },
            },
        ]
        summary = get_hosts_summary(hosts)
        assert "host_count" in summary
        assert 3 == summary["host_count"]

        assert_is_not_multiarch(summary)
        assert "mixed" == summary["iso_type"]


def assert_is_multiarch(summary):
    assert "heterogeneous_arch" in summary
    assert summary["heterogeneous_arch"]


def assert_is_not_multiarch(summary):
    assert "heterogeneous_arch" in summary
    assert not summary["heterogeneous_arch"]
