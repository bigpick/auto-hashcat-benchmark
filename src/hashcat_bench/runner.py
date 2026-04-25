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
        priv = Path(env_path).expanduser()
        if priv.suffix == ".pub":
            priv = priv.with_suffix("")
        if priv.exists():
            return priv

    ssh_dir = Path.home() / ".ssh"
    for name in ("id_ed25519_vast_ai", "id_ed25519", "id_rsa"):
        path = ssh_dir / name
        if path.exists():
            return path

    keys = list(ssh_dir.glob("id_*")) if ssh_dir.exists() else []
    private_keys = [k for k in keys if not k.suffix == ".pub"]
    if private_keys:
        raise RuntimeError(
            f"No SSH key found at standard paths. Found these keys: "
            f"{', '.join(k.name for k in private_keys)}. "
            f"Set HASHCAT_BENCH_SSH_KEY to the correct one."
        )

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
        interactive: bool = False,
    ) -> BenchmarkResult:
        key_path = _resolve_ssh_key_path()
        print(f"  Using SSH key: {key_path}")
        self._provider.ensure_ssh_key()

        cuda_major_minor = float(".".join(cuda_version.split(".")[:2]))
        offer = self._select_offer(
            vastai_name, cuda_major_minor, interactive,
        )
        if offer is None:
            raise RuntimeError(
                f"No available offers for GPU: {vastai_name} "
                f"(with CUDA >= {cuda_major_minor})"
            )

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

    def _select_offer(
        self, vastai_name: str, min_cuda: float, interactive: bool
    ) -> dict | None:
        offers = self._provider.search_gpu(vastai_name)
        viable = [
            o for o in offers
            if o.get("reliability", 0) >= 0.8
            and o.get("cpu_ram", 0) >= 16384
            and o.get("cpu_cores_effective", 0) >= 4
            and o.get("cuda_max_good", 0) >= min_cuda
        ]

        if not viable:
            if offers:
                print(f"  Found {len(offers)} offers but none meet requirements (CUDA >= {min_cuda}, RAM >= 16GB, reliability >= 0.8)")
            return None

        viable.sort(key=lambda o: o["dph_total"])

        def _fmt(o: dict, idx: str = "") -> str:
            prefix = f"  [{idx}] " if idx else "  "
            return (
                f"{prefix}ID {o.get('id', '?'):>9}  "
                f"${o['dph_total']:.3f}/hr  "
                f"CUDA {o.get('cuda_max_good', '?')}  "
                f"RAM {int(o.get('cpu_ram', 0) / 1024)}GB  "
                f"{o.get('cpu_cores_effective', '?')} cores  "
                f"reliability {o.get('reliability', 0):.0%}  "
                f"{o.get('geolocation', '?')}"
            )

        if interactive and len(viable) > 1:
            print(f"  {len(viable)} viable offers for {vastai_name}:\n")
            for i, o in enumerate(viable[:10]):
                print(_fmt(o, str(i + 1)))
            print()
            choice = input(f"  Pick [1-{min(len(viable), 10)}] or Enter for cheapest: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= min(len(viable), 10):
                selected = viable[int(choice) - 1]
            else:
                selected = viable[0]
        else:
            selected = viable[0]
            print(f"  Selected ({len(viable)} viable):")
            print(_fmt(selected))

        return selected

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
        poll_interval = 30
        max_wait = MAX_WAIT_SECONDS
        start = time.time()

        conn = self._ssh_connect_with_retry(host, port, key_path)
        try:
            while time.time() - start < max_wait:
                elapsed = int(time.time() - start)

                _, stdout, _ = conn.exec_command("cat /tmp/result.json 2>/dev/null", timeout=30)
                output = stdout.read().decode()
                if output.strip():
                    return output

                _, stdout, _ = conn.exec_command(
                    "pgrep -x hashcat >/dev/null 2>&1 && echo HASHCAT_RUNNING; "
                    "pgrep -f entrypoint >/dev/null 2>&1 && echo ENTRYPOINT_RUNNING; "
                    "echo CHECK_DONE",
                    timeout=15,
                )
                proc_output = stdout.read().decode().strip()
                hashcat_running = "HASHCAT_RUNNING" in proc_output
                entrypoint_running = "ENTRYPOINT_RUNNING" in proc_output

                if hashcat_running or entrypoint_running:
                    detail = ""
                    try:
                        _, stdout, _ = conn.exec_command(
                            "nvidia-smi --query-gpu=utilization.gpu,temperature.gpu "
                            "--format=csv,noheader,nounits 2>/dev/null",
                            timeout=10,
                        )
                        gpu_info = stdout.read().decode().strip()
                        if gpu_info:
                            parts = gpu_info.split(",")
                            gpu_util = parts[0].strip()
                            gpu_temp = parts[1].strip() if len(parts) > 1 else "?"
                            detail = f" GPU: {gpu_util}%, {gpu_temp}C"
                    except Exception:
                        pass

                    if hashcat_running:
                        phase = "hashcat running"
                    else:
                        phase = "entrypoint running (pre-benchmark)"
                    print(f"  [{elapsed}s] {phase}{' -' + detail if detail else ''}    ", end="\r")
                else:
                    _, stdout, _ = conn.exec_command("cat /tmp/result.json 2>/dev/null", timeout=30)
                    output = stdout.read().decode()
                    if output.strip():
                        print()
                        return output
                    diag = ""
                    try:
                        _, stdout, _ = conn.exec_command(
                            "ls -la /tmp/result.json 2>&1; echo '---'; "
                            "ps aux 2>&1 | head -20",
                            timeout=15,
                        )
                        diag = stdout.read().decode().strip()
                    except Exception:
                        pass
                    print()
                    raise RuntimeError(
                        "Benchmark finished but no result.json found. "
                        f"Diagnostics:\n{diag}"
                    )

                time.sleep(poll_interval)

            print()
            raise TimeoutError(f"Benchmark did not complete within {max_wait}s")
        finally:
            conn.close()

    def _ssh_connect_with_retry(self, host: str, port: int, key_path: Path) -> paramiko.SSHClient:
        max_attempts = 10
        retry_delay = 15

        for attempt in range(1, max_attempts + 1):
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
                return client
            except (paramiko.SSHException, OSError, EOFError) as e:
                client.close()
                if attempt < max_attempts:
                    print(f"  SSH not ready (attempt {attempt}/{max_attempts}): {e}")
                    time.sleep(retry_delay)
                    continue
                raise RuntimeError(f"SSH connection failed after {max_attempts} attempts: {e}")
