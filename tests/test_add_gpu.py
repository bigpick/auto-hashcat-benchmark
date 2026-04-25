import json
from pathlib import Path
from hashcat_bench.cli import add_gpu_cmd, list_gpu_families_cmd, GPU_FAMILIES


def _make_gpu_file(tmp_path, models=None):
    gpu_file = tmp_path / "gpu-models.json"
    gpu_file.write_text(json.dumps({"models": models or []}))
    return gpu_file


def test_add_single_gpu(tmp_path):
    _make_gpu_file(tmp_path)
    add_gpu_cmd(tmp_path, ["RTX 2080 Ti"], family="Turing")
    data = json.loads((tmp_path / "gpu-models.json").read_text())
    assert len(data["models"]) == 1
    assert data["models"][0]["name"] == "RTX 2080 Ti"
    assert data["models"][0]["slug"] == "rtx-2080-ti"
    assert data["models"][0]["family"] == "Turing"


def test_add_family_bulk(tmp_path):
    _make_gpu_file(tmp_path)
    add_gpu_cmd(tmp_path, ["rtx-20"])
    data = json.loads((tmp_path / "gpu-models.json").read_text())
    names = [m["name"] for m in data["models"]]
    assert "RTX 2080 Ti" in names
    assert "RTX 2060" in names
    assert len(data["models"]) == len(GPU_FAMILIES["rtx-20"])


def test_add_skips_duplicates(tmp_path):
    _make_gpu_file(tmp_path, [
        {"name": "RTX 2080 Ti", "slug": "rtx-2080-ti", "family": "Turing", "vendor": "nvidia", "vastai_name": "RTX 2080 Ti"},
    ])
    add_gpu_cmd(tmp_path, ["rtx-20"])
    data = json.loads((tmp_path / "gpu-models.json").read_text())
    slugs = [m["slug"] for m in data["models"]]
    assert slugs.count("rtx-2080-ti") == 1


def test_add_datacenter(tmp_path):
    _make_gpu_file(tmp_path)
    add_gpu_cmd(tmp_path, ["datacenter"])
    data = json.loads((tmp_path / "gpu-models.json").read_text())
    names = [m["name"] for m in data["models"]]
    assert "H100" in names
    assert "A100" in names
    assert "T4" in names


def test_gpu_families_lists_all(capsys):
    list_gpu_families_cmd()
    out = capsys.readouterr().out
    assert "rtx-20" in out
    assert "datacenter" in out
    assert "gtx-10" in out
