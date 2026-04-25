from __future__ import annotations
from hashcat_bench.models import BenchmarkEntry

HASH_MODE_NAMES: dict[int, str] = {
    0: "MD5",
    100: "SHA1",
    1400: "SHA2-256",
    1700: "SHA2-512",
    2500: "WPA-EAPOL-PBKDF2",
    3000: "LM",
    5500: "NetNTLMv1 / NetNTLMv1+ESS",
    5600: "NetNTLMv2",
    13100: "Kerberos 5, etype 23, TGS-REP",
    18200: "Kerberos 5, etype 23, AS-REP",
    22000: "WPA-PBKDF2-PMKID+EAPOL",
}

def parse_machine_readable(text: str) -> tuple[str | None, list[BenchmarkEntry]]:
    version = None
    entries: list[BenchmarkEntry] = []
    for line in text.strip().splitlines():
        line = line.strip()
        if line.startswith("# version:"):
            version = line.split(":", 1)[1].strip()
            continue
        if line.startswith("#") or not line:
            continue
        parts = line.split(":")
        if len(parts) < 6:
            continue
        hash_mode = int(parts[2])
        exec_runtime_ms = int(parts[3]) / 1000.0
        speed = int(parts[5])
        entries.append(BenchmarkEntry(
            hash_mode=hash_mode,
            hash_name=HASH_MODE_NAMES.get(hash_mode, f"mode_{hash_mode}"),
            speed=speed,
            exec_runtime_ms=exec_runtime_ms,
        ))
    return version, entries

def parse_nvidia_smi(csv_output: str) -> tuple[str, str]:
    parts = csv_output.strip().split(",")
    gpu_name = parts[0].strip()
    driver_version = parts[1].strip()
    return gpu_name, driver_version
