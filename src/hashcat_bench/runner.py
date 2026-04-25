from __future__ import annotations
import json
import time
from io import StringIO
import paramiko
from hashcat_bench.models import BenchmarkResult
from hashcat_bench.provider import VastProvider

POLL_INTERVAL_SECONDS = 15
MAX_WAIT_SECONDS = 1800


class BenchmarkRunner:
    def __init__(self, provider: VastProvider):
        self._provider = provider

    def run(
        self,
        vastai_name: str,
        image: str,
        hashcat_version: str,
        kernel_mode: str = "optimized",
        benchmark_all: bool = False,
        cuda_version: str = "12.9.1",
    ) -> BenchmarkResult:
        offer = self._provider.cheapest_offer(vastai_name)
        if offer is None:
            raise RuntimeError(f"No available offers for GPU: {vastai_name}")
        env = {
            "HASHCAT_VERSION": hashcat_version,
            "KERNEL_MODE": kernel_mode,
            "BENCHMARK_ALL": "true" if benchmark_all else "false",
            "CUDA_VERSION": cuda_version,
            "CONTAINER_IMAGE": image,
        }
        instance_id = self._provider.create_instance(offer_id=offer["id"], image=image, env=env)
        try:
            ssh_info = self._wait_for_ready(instance_id)
            output = self._collect_results(ssh_info["ssh_host"], ssh_info["ssh_port"])
            result_data = json.loads(output)
            return BenchmarkResult.from_dict(result_data)
        finally:
            self._provider.destroy_instance(instance_id)

    def _wait_for_ready(self, instance_id: int) -> dict:
        start = time.time()
        while time.time() - start < MAX_WAIT_SECONDS:
            status = self._provider.instance_status(instance_id)
            if status.get("actual_status") == "running" and status.get("ssh_host"):
                return status
            time.sleep(POLL_INTERVAL_SECONDS)
        raise TimeoutError(f"Instance {instance_id} did not become ready within {MAX_WAIT_SECONDS}s")

    def _collect_results(self, host: str, port: int) -> str:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(host, port=port, username="root", timeout=30)
            _, stdout, stderr = client.exec_command("cat /tmp/result.json", timeout=60)
            return stdout.read().decode()
        finally:
            client.close()
