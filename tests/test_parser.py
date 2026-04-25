from hashcat_bench.parser import parse_machine_readable, parse_nvidia_smi
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent / "fixtures"

def test_parse_machine_readable():
    text = (FIXTURE_DIR / "hashcat_machine_readable.txt").read_text()
    version, entries = parse_machine_readable(text)
    assert version == "6.2.6"
    assert len(entries) == 5
    assert entries[0].hash_mode == 0
    assert entries[0].speed == 164_000_000_000
    assert entries[0].exec_runtime_ms == 12.5

def test_parse_machine_readable_extracts_exec_runtime():
    text = (FIXTURE_DIR / "hashcat_machine_readable.txt").read_text()
    _, entries = parse_machine_readable(text)
    assert entries[2].exec_runtime_ms == 22.1

def test_parse_machine_readable_no_version():
    text = "1:0:0:12500:55.02:164000000000\n"
    version, entries = parse_machine_readable(text)
    assert version is None
    assert len(entries) == 1

def test_parse_nvidia_smi():
    csv_output = "NVIDIA GeForce RTX 4090, 535.129.03, 24564 MiB\n"
    gpu_name, driver_version = parse_nvidia_smi(csv_output)
    assert gpu_name == "NVIDIA GeForce RTX 4090"
    assert driver_version == "535.129.03"

def test_parse_nvidia_smi_strips_whitespace():
    csv_output = "  NVIDIA GeForce RTX 3080 ,  525.85.12 , 10240 MiB  \n"
    gpu_name, driver_version = parse_nvidia_smi(csv_output)
    assert gpu_name == "NVIDIA GeForce RTX 3080"
    assert driver_version == "525.85.12"
