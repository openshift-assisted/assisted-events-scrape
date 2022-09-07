from process import get_hosts_summary, reshape_host


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

    def test_reshape_host(self):
        host = get_host_with_inventory()
        reshape_host(host)
        assert "inventory" not in host
        assert "host_inventory" in host
        assert "bmc_address" in host["host_inventory"]
        assert "0.0.0.0" == host["host_inventory"]["bmc_address"]
        assert "cpu" in host["host_inventory"] and "count" in host["host_inventory"]["cpu"]
        assert 4 == host["host_inventory"]["cpu"]["count"]


def assert_is_multiarch(summary):
    assert "heterogeneous_arch" in summary
    assert summary["heterogeneous_arch"]


def assert_is_not_multiarch(summary):
    assert "heterogeneous_arch" in summary
    assert not summary["heterogeneous_arch"]


def get_host_with_inventory():
    host = {
        "id": "dfa379ed-801c-4765-b638-cc67f3e87cf2",
        "infra_env_id": "39b315e3-f9d4-4869-8927-a6d56c26c5ac",
        "installation_disk_id": "/dev/disk/by-path/pci-0000:00:06.0",
        "installation_disk_path": "/dev/vda",
        "inventory": "{\"bmc_address\":\"0.0.0.0\",\"bmc_v6address\":\"::/0\",\"boot\":{\"current_boot_mode\":\"bios\"},\"cpu\":{\"architecture\":\"x86_64\",\"count\":4,\"flags\":[\"fpu\",\"vme\",\"de\",\"pse\",\"tsc\",\"msr\",\"pae\",\"mce\",\"cx8\",\"apic\",\"sep\",\"mtrr\",\"pge\",\"mca\",\"cmov\",\"pat\",\"pse36\",\"clflush\",\"mmx\",\"fxsr\",\"sse\",\"sse2\",\"ss\",\"syscall\",\"nx\",\"pdpe1gb\",\"rdtscp\",\"lm\",\"constant_tsc\",\"arch_perfmon\",\"rep_good\",\"nopl\",\"xtopology\",\"cpuid\",\"tsc_known_freq\",\"pni\",\"pclmulqdq\",\"vmx\",\"ssse3\",\"fma\",\"cx16\",\"pcid\",\"sse4_1\",\"sse4_2\",\"x2apic\",\"movbe\",\"popcnt\",\"tsc_deadline_timer\",\"aes\",\"xsave\",\"avx\",\"f16c\",\"rdrand\",\"hypervisor\",\"lahf_lm\",\"abm\",\"3dnowprefetch\",\"cpuid_fault\",\"invpcid_single\",\"pti\",\"ssbd\",\"ibrs\",\"ibpb\",\"stibp\",\"tpr_shadow\",\"vnmi\",\"flexpriority\",\"ept\",\"vpid\",\"ept_ad\",\"fsgsbase\",\"tsc_adjust\",\"bmi1\",\"hle\",\"avx2\",\"smep\",\"bmi2\",\"erms\",\"invpcid\",\"rtm\",\"mpx\",\"avx512f\",\"avx512dq\",\"rdseed\",\"adx\",\"smap\",\"clflushopt\",\"clwb\",\"avx512cd\",\"avx512bw\",\"avx512vl\",\"xsaveopt\",\"xsavec\",\"xgetbv1\",\"xsaves\",\"arat\",\"umip\",\"pku\",\"ospke\",\"md_clear\",\"arch_capabilities\"],\"frequency\":2095.076,\"model_name\":\"Intel(R) Xeon(R) Gold 6130 CPU @ 2.10GHz\"},\"disks\":[{\"by_path\":\"/dev/disk/by-path/pci-0000:00:01.1-ata-1\",\"drive_type\":\"ODD\",\"hctl\":\"0:0:0:0\",\"id\":\"/dev/disk/by-path/pci-0000:00:01.1-ata-1\",\"installation_eligibility\":{\"not_eligible_reasons\":[\"Disk is removable\",\"Disk is too small (disk only has 109 MB, but 20 GB are required)\",\"Drive type is ODD, it must be one of HDD, SSD.\"]},\"is_installation_media\":true,\"model\":\"QEMU_DVD-ROM\",\"name\":\"sr0\",\"path\":\"/dev/sr0\",\"removable\":true,\"serial\":\"QM00001\",\"size_bytes\":108984320,\"smart\":\"{\\\"json_format_version\\\":[1,0],\\\"smartctl\\\":{\\\"version\\\":[7,1],\\\"svn_revision\\\":\\\"5049\\\",\\\"platform_info\\\":\\\"x86_64-linux-4.18.0-305.19.1.el8_4.x86_64\\\",\\\"build_info\\\":\\\"(local build)\\\",\\\"argv\\\":[\\\"smartctl\\\",\\\"--xall\\\",\\\"--json=c\\\",\\\"/dev/sr0\\\"],\\\"exit_status\\\":4},\\\"device\\\":{\\\"name\\\":\\\"/dev/sr0\\\",\\\"info_name\\\":\\\"/dev/sr0\\\",\\\"type\\\":\\\"scsi\\\",\\\"protocol\\\":\\\"SCSI\\\"},\\\"vendor\\\":\\\"QEMU\\\",\\\"product\\\":\\\"QEMU DVD-ROM\\\",\\\"model_name\\\":\\\"QEMU QEMU DVD-ROM\\\",\\\"revision\\\":\\\"2.5+\\\",\\\"scsi_version\\\":\\\"SPC-3\\\",\\\"device_type\\\":{\\\"scsi_value\\\":5,\\\"name\\\":\\\"CD/DVD\\\"},\\\"local_time\\\":{\\\"time_t\\\":1646746247,\\\"asctime\\\":\\\"Tue Mar  8 13:30:47 2022 UTC\\\"},\\\"temperature\\\":{\\\"current\\\":0,\\\"drive_trip\\\":0}}\",\"vendor\":\"QEMU\"},{\"by_path\":\"/dev/disk/by-path/pci-0000:00:06.0\",\"drive_type\":\"HDD\",\"id\":\"/dev/disk/by-path/pci-0000:00:06.0\",\"installation_eligibility\":{\"eligible\":true,\"not_eligible_reasons\":null},\"name\":\"vda\",\"path\":\"/dev/vda\",\"size_bytes\":128849018880,\"smart\":\"{\\\"json_format_version\\\":[1,0],\\\"smartctl\\\":{\\\"version\\\":[7,1],\\\"svn_revision\\\":\\\"5049\\\",\\\"platform_info\\\":\\\"x86_64-linux-4.18.0-305.19.1.el8_4.x86_64\\\",\\\"build_info\\\":\\\"(local build)\\\",\\\"argv\\\":[\\\"smartctl\\\",\\\"--xall\\\",\\\"--json=c\\\",\\\"/dev/vda\\\"],\\\"messages\\\":[{\\\"string\\\":\\\"/dev/vda: Unable to detect device type\\\",\\\"severity\\\":\\\"error\\\"}],\\\"exit_status\\\":1}}\",\"vendor\":\"0x1af4\"}],\"gpus\":[{\"address\":\"0000:00:02.0\",\"device_id\":\"00b8\",\"name\":\"GD 5446\",\"vendor\":\"Cirrus Logic\",\"vendor_id\":\"1013\"}],\"hostname\":\"test-infra-cluster-c8f19e82-master-2\",\"interfaces\":[{\"flags\":[\"up\",\"broadcast\",\"multicast\"],\"has_carrier\":true,\"ipv4_addresses\":[\"192.168.133.12/24\"],\"ipv6_addresses\":[],\"mac_address\":\"02:00:00:70:99:71\",\"mtu\":1500,\"name\":\"ens3\",\"product\":\"0x0001\",\"speed_mbps\":-1,\"vendor\":\"0x1af4\"},{\"flags\":[\"up\",\"broadcast\",\"multicast\"],\"has_carrier\":true,\"ipv4_addresses\":[\"192.168.151.12/24\"],\"ipv6_addresses\":[],\"mac_address\":\"02:00:00:bb:18:d9\",\"mtu\":1500,\"name\":\"ens4\",\"product\":\"0x0001\",\"speed_mbps\":-1,\"vendor\":\"0x1af4\"}],\"memory\":{\"physical_bytes\":17809014784,\"physical_bytes_method\":\"dmidecode\",\"usable_bytes\":17421824000},\"routes\":[{\"destination\":\"0.0.0.0\",\"family\":2,\"gateway\":\"192.168.133.1\",\"interface\":\"ens3\"},{\"destination\":\"0.0.0.0\",\"family\":2,\"gateway\":\"192.168.151.1\",\"interface\":\"ens4\"},{\"destination\":\"10.88.0.0\",\"family\":2,\"interface\":\"cni-podman0\"},{\"destination\":\"192.168.133.0\",\"family\":2,\"interface\":\"ens3\"},{\"destination\":\"192.168.151.0\",\"family\":2,\"interface\":\"ens4\"},{\"destination\":\"::1\",\"family\":10,\"interface\":\"lo\"},{\"destination\":\"fe80::\",\"family\":10,\"interface\":\"ens3\"},{\"destination\":\"fe80::\",\"family\":10,\"interface\":\"ens4\"},{\"destination\":\"fe80::\",\"family\":10,\"interface\":\"cni-podman0\"}],\"system_vendor\":{\"manufacturer\":\"Red Hat\",\"product_name\":\"KVM\",\"virtual\":true},\"timestamp\":1646746247,\"tpm_version\":\"none\"}"  # noqa: E501
    }
    return host
