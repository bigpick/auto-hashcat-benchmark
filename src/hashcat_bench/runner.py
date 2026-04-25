from __future__ import annotations

import json
import os
import time
from pathlib import Path

import paramiko

from hashcat_bench.models import BenchmarkResult
from hashcat_bench.provider import VastProvider

POLL_INTERVAL_SECONDS = 15
MAX_WAIT_SECONDS = 1800


def _resolve_ssh_key_path() -> Path:
    env_path = os.environ.get("HASHCAT_BENCH_SSH_KEY")
    if env_path:
        priv = Path(env_path)
        if priv.suffix == ".pub":
            priv = priv.with_suffix("")
        if priv.exists():
            return priv

    for name in ("id_ed25519", "id_rsa"):
        path = Path.home() / ".ssh" / name
        if path.exists():
            return path

    raise RuntimeError(
        "No SSH private key found. Set HASHCAT_BENCH_SSH_KEY or ensure "
        "~/.ssh/id_ed25519 or ~/.ssh/id_rsa exists."
    )


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
        self._provider.ensure_ssh_key()

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

        instance_id = self._provider.create_instance(
            offer_id=offer["id"],
            image=image,
            env=env,
        )
        print(f"  Instance {instance_id} created (offer {offer['id']}, ${offer['dph_total']:.3f}/hr)")

        try:
            ssh_info = self._wait_for_ready(instance_id)
            print(f"  Instance ready, collecting results via SSH...")
            output = self._collect_results(ssh_info["ssh_host"], ssh_info["ssh_port"])
            result_data = json.loads(output)
            return BenchmarkResult.from_dict(result_data)
        finally:
            print(f"  Destroying instance {instance_id}...")
            self._provider.destroy_instance(instance_id)

    def _wait_for_ready(self, instance_id: int) -> dict:
        start = time.time()
        last_msg = ""
        last_change = time.time()
        stale_timeout = 600

        while time.time() - start < MAX_WAIT_SECONDS:
            status = self._provider.instance_status(instance_id)
            actual = status.get("actual_status", "unknown")
            status_msg = status.get("status_msg", "")
            elapsed = int(time.time() - start)
            display = f"  [{elapsed}s] status: {actual}"
            if status_msg:
                display += f" - {status_msg[:60]}"
            print(display + "    ", end="\r")

            if actual == "running" and status.get("ssh_host"):
                print()
                return status

            if actual in ("exited", "error"):
                print()
                raise RuntimeError(
                    f"Instance {instance_id} failed (status: {actual}). "
                    f"Message: {status_msg}"
                )

            if status_msg != last_msg:
                last_msg = status_msg
                last_change = time.time()
            elif time.time() - last_change > stale_timeout:
                print()
                raise RuntimeError(
                    f"Instance {instance_id} has shown no progress for {stale_timeout // 60} minutes. "
                    f"Last message: {status_msg}"
                )

            time.sleep(POLL_INTERVAL_SECONDS)
        raise TimeoutError(f"Instance {instance_id} did not become ready within {MAX_WAIT_SECONDS}s")

    def _collect_results(self, host: str, port: int) -> str:
        key_path = _resolve_ssh_key_path()
        max_ssh_attempts = 12
        ssh_retry_delay = 15

        for attempt in range(1, max_ssh_attempts + 1):
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(
                    host,
                    port=port,
                    username="root",
                    key_filename=str(key_path),
                    timeout=30,
                    banner_timeout=30,
                )
                _, stdout, stderr = client.exec_command("cat /tmp/result.json", timeout=120)
                output = stdout.read().decode()
                if not output.strip():
                    err = stderr.read().decode()
                    if attempt < max_ssh_attempts:
                        print(f"  result.json not ready yet (attempt {attempt}/{max_ssh_attempts}), waiting...")
                        time.sleep(ssh_retry_delay)
                        continue
                    raise RuntimeError(f"No result.json found on instance after {max_ssh_attempts} attempts. stderr: {err}")
                return output
            except (paramiko.SSHException, OSError, EOFError) as e:
                if attempt < max_ssh_attempts:
                    print(f"  SSH not ready (attempt {attempt}/{max_ssh_attempts}): {e}")
                    time.sleep(ssh_retry_delay)
                    continue
                raise RuntimeError(f"SSH connection failed after {max_ssh_attempts} attempts: {e}")
            finally:
                client.close()
