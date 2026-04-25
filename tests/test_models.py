from hashcat_bench.models import (
    BenchmarkEntry,
    BenchmarkResult,
    GpuModel,
    GpuModelRegistry,
)
import json
from pathlib import Path


def test_benchmark_entry_creation():
    entry = BenchmarkEntry(hash_mode=0, hash_name="MD5", speed=164_000_000_000, exec_runtime_ms=12.5)
    assert entry.hash_mode == 0
    assert entry.speed == 164_000_000_000


def test_benchmark_result_to_dict():
    result = BenchmarkResult(
        hashcat_version="v6.2.6",
        gpu_model="RTX 4090",
        container_image="ghcr.io/user/hashcat-bench:v6.2.6-cuda12.2",
        driver_version="535.129.03",
        cuda_version="12.2",
        kernel_mode="optimized",
        benchmark_date="2026-04-25T14:30:00Z",
        benchmarks=[
            BenchmarkEntry(hash_mode=0, hash_name="MD5", speed=164_000_000_000, exec_runtime_ms=12.5),
        ],
    )
    d = result.to_dict()
    assert d["hashcat_version"] == "v6.2.6"
    assert d["benchmarks"][0]["hash_mode"] == 0
    parsed = json.loads(json.dumps(d))
    assert parsed == d


def test_benchmark_result_from_dict():
    d = {
        "hashcat_version": "v6.2.6",
        "gpu_model": "RTX 4090",
        "container_image": "ghcr.io/user/hashcat-bench:v6.2.6-cuda12.2",
        "driver_version": "535.129.03",
        "cuda_version": "12.2",
        "kernel_mode": "optimized",
        "benchmark_date": "2026-04-25T14:30:00Z",
        "benchmarks": [
            {"hash_mode": 0, "hash_name": "MD5", "speed": 164_000_000_000, "exec_runtime_ms": 12.5},
        ],
    }
    result = BenchmarkResult.from_dict(d)
    assert result.gpu_model == "RTX 4090"
    assert result.benchmarks[0].hash_name == "MD5"


def test_gpu_model_slug():
    model = GpuModel(name="RTX 4090", slug="rtx-4090", family="Ada Lovelace", vendor="nvidia", vastai_name="RTX 4090")
    assert model.slug == "rtx-4090"


def test_benchmark_result_file_slug_optimized():
    result = BenchmarkResult(
        hashcat_version="v6.2.6",
        gpu_model="RTX 4090",
        container_image="img",
        driver_version="535",
        cuda_version="12.2",
        kernel_mode="optimized",
        benchmark_date="2026-04-25T14:30:00Z",
        benchmarks=[],
    )
    assert result.file_slug == "rtx-4090"


def test_benchmark_result_file_slug_default():
    result = BenchmarkResult(
        hashcat_version="v6.2.6",
        gpu_model="RTX 4090",
        container_image="img",
        driver_version="535",
        cuda_version="12.2",
        kernel_mode="default",
        benchmark_date="2026-04-25T14:30:00Z",
        benchmarks=[],
    )
    assert result.file_slug == "rtx-4090-default"


def test_gpu_model_registry_load(tmp_path):
    gpu_file = tmp_path / "gpu-models.json"
    gpu_file.write_text(json.dumps({
        "models": [
            {"name": "RTX 4090", "slug": "rtx-4090", "family": "Ada Lovelace", "vendor": "nvidia", "vastai_name": "RTX 4090"},
        ]
    }))
    registry = GpuModelRegistry.load(gpu_file)
    assert len(registry.models) == 1
    assert registry.get_by_slug("rtx-4090").name == "RTX 4090"
    assert registry.get_by_slug("nonexistent") is None
