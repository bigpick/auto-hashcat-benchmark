import json
from pathlib import Path
from hashcat_bench.data import DataManager
from hashcat_bench.models import BenchmarkEntry, BenchmarkResult

def _make_result(version="v6.2.6", gpu="RTX 4090", mode="optimized") -> BenchmarkResult:
    return BenchmarkResult(
        hashcat_version=version, gpu_model=gpu, container_image="img:latest",
        driver_version="535.129.03", cuda_version="12.2", kernel_mode=mode,
        benchmark_date="2026-04-25T14:30:00Z",
        benchmarks=[
            BenchmarkEntry(hash_mode=0, hash_name="MD5", speed=164_000_000_000, exec_runtime_ms=12.5),
            BenchmarkEntry(hash_mode=100, hash_name="SHA1", speed=56_000_000_000, exec_runtime_ms=18.2),
        ],
    )

def test_result_exists_false(tmp_path):
    dm = DataManager(data_dir=tmp_path)
    assert dm.result_exists("v6.2.6", "rtx-4090", "optimized") is False

def test_save_and_exists(tmp_path):
    dm = DataManager(data_dir=tmp_path)
    result = _make_result()
    dm.save_result(result)
    assert dm.result_exists("v6.2.6", "rtx-4090", "optimized") is True
    path = tmp_path / "results" / "v6.2.6" / "rtx-4090.json"
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["gpu_model"] == "RTX 4090"
    assert len(data["benchmarks"]) == 2

def test_save_default_mode(tmp_path):
    dm = DataManager(data_dir=tmp_path)
    result = _make_result(mode="default")
    dm.save_result(result)
    assert dm.result_exists("v6.2.6", "rtx-4090-default", "default") is True
    path = tmp_path / "results" / "v6.2.6" / "rtx-4090-default.json"
    assert path.exists()

def test_build_index(tmp_path):
    dm = DataManager(data_dir=tmp_path)
    dm.save_result(_make_result("v6.2.6", "RTX 4090"))
    dm.save_result(_make_result("v6.2.6", "RTX 3080"))
    dm.save_result(_make_result("v6.2.5", "RTX 4090"))
    index = dm.build_index()
    assert "v6.2.6" in index["versions"]
    assert "v6.2.5" in index["versions"]
    assert "RTX 4090" in index["gpu_models"]
    assert "RTX 3080" in index["gpu_models"]
    assert len(index["results"]) == 3
    assert any(m["mode"] == 0 and m["name"] == "MD5" for m in index["hash_modes"])

def test_build_index_writes_file(tmp_path):
    dm = DataManager(data_dir=tmp_path)
    dm.save_result(_make_result())
    dm.build_index()
    index_path = tmp_path / "index.json"
    assert index_path.exists()
    data = json.loads(index_path.read_text())
    assert "generated_at" in data

def test_list_missing(tmp_path):
    dm = DataManager(data_dir=tmp_path)
    dm.save_result(_make_result("v6.2.6", "RTX 4090"))
    slugs = ["rtx-4090", "rtx-3080"]
    missing = dm.list_missing("v6.2.6", slugs, "optimized")
    assert missing == ["rtx-3080"]
