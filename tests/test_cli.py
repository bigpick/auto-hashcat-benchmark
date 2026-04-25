import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from hashcat_bench.cli import build_index_cmd, status_cmd

def test_build_index_cmd(tmp_path):
    results_dir = tmp_path / "results" / "v6.2.6"
    results_dir.mkdir(parents=True)
    (results_dir / "rtx-4090.json").write_text(json.dumps({
        "hashcat_version": "v6.2.6", "gpu_model": "RTX 4090", "container_image": "img",
        "driver_version": "535", "cuda_version": "12.2", "kernel_mode": "optimized",
        "benchmark_date": "2026-04-25T14:30:00Z",
        "benchmarks": [{"hash_mode": 0, "hash_name": "MD5", "speed": 164000000000, "exec_runtime_ms": 12.5}],
    }))
    build_index_cmd(data_dir=tmp_path)
    index = json.loads((tmp_path / "index.json").read_text())
    assert len(index["results"]) == 1

def test_status_cmd(tmp_path, capsys):
    gpu_file = tmp_path / "gpu-models.json"
    gpu_file.write_text(json.dumps({
        "models": [
            {"name": "RTX 4090", "slug": "rtx-4090", "family": "Ada Lovelace", "vendor": "nvidia", "vastai_name": "RTX 4090"},
            {"name": "RTX 3080", "slug": "rtx-3080", "family": "Ampere", "vendor": "nvidia", "vastai_name": "RTX 3080"},
        ]
    }))
    results_dir = tmp_path / "results" / "v6.2.6"
    results_dir.mkdir(parents=True)
    (results_dir / "rtx-4090.json").write_text('{"hashcat_version":"v6.2.6"}')
    status_cmd(data_dir=tmp_path, versions=["v6.2.6"])
    captured = capsys.readouterr()
    assert "rtx-4090" in captured.out
    assert "rtx-3080" in captured.out
