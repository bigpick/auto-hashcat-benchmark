# Hashcat GPU Benchmark Hub — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a repository with automated GPU benchmarking infrastructure and a GitHub Pages dashboard for visualizing hashcat speed benchmarks across GPU models and hashcat versions.

**Architecture:** Local Python CLI orchestrates Vast.ai GPU rentals, runs containerized hashcat benchmarks, and writes structured JSON results to the repo. GitHub Actions builds a consolidated index and deploys a Svelte single-page dashboard to GitHub Pages. Justfile provides the command interface.

**Tech Stack:** Python 3.12+ (uv), Vast.ai SDK, Docker (nvidia/cuda base), Svelte 5 + Vite, Chart.js, GitHub Actions, Just

**Note:** The repo owner handles all git operations. No tasks include git commit/push steps.

---

## File Map

| File | Responsibility |
|------|---------------|
| `pyproject.toml` | Python project config, dependencies, uv managed |
| `Justfile` | Command interface for all operations |
| `.gitignore` | Ignore patterns |
| `src/hashcat_bench/__init__.py` | Package init |
| `src/hashcat_bench/models.py` | Dataclasses for benchmark results, GPU models |
| `src/hashcat_bench/parser.py` | Parse hashcat machine-readable output → dataclasses |
| `src/hashcat_bench/data.py` | Read/write result files, idempotency check, build index |
| `src/hashcat_bench/provider.py` | Vast.ai SDK wrapper: search, rent, destroy |
| `src/hashcat_bench/estimator.py` | Cost estimation from Vast.ai pricing |
| `src/hashcat_bench/runner.py` | SSH into instance, run container, collect results |
| `src/hashcat_bench/cli.py` | CLI entrypoint wiring all modules |
| `container/Dockerfile` | hashcat benchmark image |
| `container/entrypoint.sh` | Run benchmark, collect GPU info, output JSON |
| `data/gpu-models.json` | Canonical GPU model list |
| `data/results/` | Benchmark result JSON files (one per version/gpu) |
| `site/` | Svelte + Vite frontend |
| `.github/workflows/deploy.yml` | Build index + site, deploy to Pages |
| `tests/` | Python test suite |

---

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.python-version`
- Create: `src/hashcat_bench/__init__.py`
- Create: `Justfile`
- Create: `data/gpu-models.json`
- Create: `data/results/.gitkeep`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "hashcat-bench"
version = "0.1.0"
description = "Automated hashcat GPU benchmark orchestrator"
requires-python = ">=3.12"
dependencies = [
    "vastai>=1.0",
    "paramiko>=3.4",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
]

[project.scripts]
hashcat-bench = "hashcat_bench.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 2: Create .python-version**

```
3.12
```

- [ ] **Step 3: Create .gitignore**

```gitignore
__pycache__/
*.pyc
.venv/
*.egg-info/
dist/
.superpowers/
.remember/
node_modules/
site/dist/
data/index.json
.pytest_cache/
.coverage
```

- [ ] **Step 4: Create src/hashcat_bench/__init__.py**

```python
"""Automated hashcat GPU benchmark orchestrator."""
```

- [ ] **Step 5: Create initial Justfile**

```just
set dotenv-load

python := "uv run"

# Setup
setup:
    uv sync --all-extras

# Run tests
test *ARGS:
    {{ python }} pytest tests/ {{ ARGS }}

# Run tests with coverage
test-cov:
    {{ python }} pytest tests/ --cov=hashcat_bench --cov-report=term-missing
```

- [ ] **Step 6: Create data/gpu-models.json**

```json
{
  "models": [
    {"name": "RTX 5090", "slug": "rtx-5090", "family": "Blackwell", "vendor": "nvidia", "vastai_name": "RTX 5090"},
    {"name": "RTX 5080", "slug": "rtx-5080", "family": "Blackwell", "vendor": "nvidia", "vastai_name": "RTX 5080"},
    {"name": "RTX 5070 Ti", "slug": "rtx-5070-ti", "family": "Blackwell", "vendor": "nvidia", "vastai_name": "RTX 5070 Ti"},
    {"name": "RTX 5070", "slug": "rtx-5070", "family": "Blackwell", "vendor": "nvidia", "vastai_name": "RTX 5070"},
    {"name": "RTX 4090", "slug": "rtx-4090", "family": "Ada Lovelace", "vendor": "nvidia", "vastai_name": "RTX 4090"},
    {"name": "RTX 4080", "slug": "rtx-4080", "family": "Ada Lovelace", "vendor": "nvidia", "vastai_name": "RTX 4080"},
    {"name": "RTX 4070 Ti", "slug": "rtx-4070-ti", "family": "Ada Lovelace", "vendor": "nvidia", "vastai_name": "RTX 4070 Ti"},
    {"name": "RTX 4070", "slug": "rtx-4070", "family": "Ada Lovelace", "vendor": "nvidia", "vastai_name": "RTX 4070"},
    {"name": "RTX 4060 Ti", "slug": "rtx-4060-ti", "family": "Ada Lovelace", "vendor": "nvidia", "vastai_name": "RTX 4060 Ti"},
    {"name": "RTX 4060", "slug": "rtx-4060", "family": "Ada Lovelace", "vendor": "nvidia", "vastai_name": "RTX 4060"},
    {"name": "RTX 3090", "slug": "rtx-3090", "family": "Ampere", "vendor": "nvidia", "vastai_name": "RTX 3090"},
    {"name": "RTX 3080", "slug": "rtx-3080", "family": "Ampere", "vendor": "nvidia", "vastai_name": "RTX 3080"},
    {"name": "RTX 3070", "slug": "rtx-3070", "family": "Ampere", "vendor": "nvidia", "vastai_name": "RTX 3070"},
    {"name": "RTX 3060", "slug": "rtx-3060", "family": "Ampere", "vendor": "nvidia", "vastai_name": "RTX 3060"}
  ]
}
```

- [ ] **Step 7: Create data/results/.gitkeep**

Empty file to track the directory.

- [ ] **Step 8: Initialize uv environment and verify**

Run: `uv sync --all-extras`
Expected: Virtual environment created, dependencies installed.

Run: `uv run python -c "import hashcat_bench; print('ok')"`
Expected: Prints `ok`

---

## Task 2: Data Models

**Files:**
- Create: `src/hashcat_bench/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write tests for data models**

Create `tests/test_models.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `just test tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'hashcat_bench.models'`

- [ ] **Step 3: Implement models**

Create `src/hashcat_bench/models.py`:

```python
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class BenchmarkEntry:
    hash_mode: int
    hash_name: str
    speed: int
    exec_runtime_ms: float


@dataclass
class BenchmarkResult:
    hashcat_version: str
    gpu_model: str
    container_image: str
    driver_version: str
    cuda_version: str
    kernel_mode: str
    benchmark_date: str
    benchmarks: list[BenchmarkEntry] = field(default_factory=list)

    @property
    def file_slug(self) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", self.gpu_model.lower()).strip("-")
        if self.kernel_mode == "default":
            slug += "-default"
        return slug

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> BenchmarkResult:
        benchmarks = [BenchmarkEntry(**b) for b in d.get("benchmarks", [])]
        return cls(
            hashcat_version=d["hashcat_version"],
            gpu_model=d["gpu_model"],
            container_image=d["container_image"],
            driver_version=d["driver_version"],
            cuda_version=d["cuda_version"],
            kernel_mode=d["kernel_mode"],
            benchmark_date=d["benchmark_date"],
            benchmarks=benchmarks,
        )


@dataclass
class GpuModel:
    name: str
    slug: str
    family: str
    vendor: str
    vastai_name: str


@dataclass
class GpuModelRegistry:
    models: list[GpuModel]

    @classmethod
    def load(cls, path: Path) -> GpuModelRegistry:
        data = json.loads(path.read_text())
        models = [GpuModel(**m) for m in data["models"]]
        return cls(models=models)

    def get_by_slug(self, slug: str) -> GpuModel | None:
        for m in self.models:
            if m.slug == slug:
                return m
        return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `just test tests/test_models.py -v`
Expected: All 7 tests PASS

---

## Task 3: Hashcat Output Parser

**Files:**
- Create: `src/hashcat_bench/parser.py`
- Create: `tests/test_parser.py`
- Create: `tests/fixtures/hashcat_machine_readable.txt`

- [ ] **Step 1: Create test fixture**

Create `tests/fixtures/hashcat_machine_readable.txt`:

```
# version: 6.2.6
# option: --optimized-kernel-enable
1:0:0:12500:55.02:164000000000
1:0:100:18200:55.02:56000000000
1:0:1400:22100:55.02:22100000000
1:0:1700:35600:55.02:8050000000
1:0:22000:142000:55.02:1200000
```

- [ ] **Step 2: Write parser tests**

Create `tests/test_parser.py`:

```python
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
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `just test tests/test_parser.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'hashcat_bench.parser'`

- [ ] **Step 4: Implement parser**

Create `src/hashcat_bench/parser.py`:

```python
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `just test tests/test_parser.py -v`
Expected: All 5 tests PASS

---

## Task 4: Data Manager

**Files:**
- Create: `src/hashcat_bench/data.py`
- Create: `tests/test_data.py`

- [ ] **Step 1: Write data manager tests**

Create `tests/test_data.py`:

```python
import json
from pathlib import Path

from hashcat_bench.data import DataManager
from hashcat_bench.models import BenchmarkEntry, BenchmarkResult


def _make_result(version="v6.2.6", gpu="RTX 4090", mode="optimized") -> BenchmarkResult:
    return BenchmarkResult(
        hashcat_version=version,
        gpu_model=gpu,
        container_image="img:latest",
        driver_version="535.129.03",
        cuda_version="12.2",
        kernel_mode=mode,
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `just test tests/test_data.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'hashcat_bench.data'`

- [ ] **Step 3: Implement data manager**

Create `src/hashcat_bench/data.py`:

```python
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from hashcat_bench.models import BenchmarkResult


class DataManager:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.results_dir = data_dir / "results"

    def _result_path(self, version: str, file_slug: str) -> Path:
        return self.results_dir / version / f"{file_slug}.json"

    def result_exists(self, version: str, file_slug: str, kernel_mode: str) -> bool:
        return self._result_path(version, file_slug).exists()

    def save_result(self, result: BenchmarkResult) -> Path:
        path = self._result_path(result.hashcat_version, result.file_slug)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result.to_dict(), indent=2) + "\n")
        return path

    def load_all_results(self) -> list[BenchmarkResult]:
        results = []
        if not self.results_dir.exists():
            return results
        for json_file in sorted(self.results_dir.rglob("*.json")):
            data = json.loads(json_file.read_text())
            results.append(BenchmarkResult.from_dict(data))
        return results

    def build_index(self) -> dict:
        results = self.load_all_results()

        versions = sorted({r.hashcat_version for r in results}, reverse=True)
        gpu_models = sorted({r.gpu_model for r in results})

        hash_modes_seen: dict[int, str] = {}
        for r in results:
            for b in r.benchmarks:
                hash_modes_seen[b.hash_mode] = b.hash_name
        hash_modes = [{"mode": m, "name": n} for m, n in sorted(hash_modes_seen.items())]

        index = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "versions": versions,
            "gpu_models": gpu_models,
            "hash_modes": hash_modes,
            "results": [r.to_dict() for r in results],
        }

        index_path = self.data_dir / "index.json"
        index_path.write_text(json.dumps(index, indent=2) + "\n")
        return index

    def list_missing(self, version: str, gpu_slugs: list[str], kernel_mode: str) -> list[str]:
        missing = []
        for slug in gpu_slugs:
            file_slug = slug if kernel_mode == "optimized" else f"{slug}-default"
            if not self.result_exists(version, file_slug, kernel_mode):
                missing.append(slug)
        return missing
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `just test tests/test_data.py -v`
Expected: All 6 tests PASS

---

## Task 5: Container Image

**Files:**
- Create: `container/Dockerfile`
- Create: `container/entrypoint.sh`

- [ ] **Step 1: Create Dockerfile**

Create `container/Dockerfile`:

```dockerfile
FROM nvidia/cuda:12.2.0-devel-ubuntu22.04

ARG HASHCAT_VERSION=v6.2.6

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        git \
        ca-certificates \
        jq \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/hashcat/hashcat.git /opt/hashcat && \
    cd /opt/hashcat && \
    git checkout ${HASHCAT_VERSION} && \
    make -j$(nproc) && \
    make install && \
    rm -rf /opt/hashcat

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
```

- [ ] **Step 2: Create entrypoint script**

Create `container/entrypoint.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

KERNEL_MODE="${KERNEL_MODE:-optimized}"
HASHCAT_VERSION="${HASHCAT_VERSION:-unknown}"
CONTAINER_IMAGE="${CONTAINER_IMAGE:-unknown}"
CUDA_VERSION="${CUDA_VERSION:-12.2}"

gpu_info=$(nvidia-smi --query-gpu=name,driver_version --format=csv,noheader)
gpu_name=$(echo "$gpu_info" | cut -d',' -f1 | xargs)
driver_version=$(echo "$gpu_info" | cut -d',' -f2 | xargs)

hashcat_flags="-b --machine-readable"
if [ "$KERNEL_MODE" = "optimized" ]; then
    hashcat_flags="$hashcat_flags -O"
fi

benchmark_output=$(hashcat $hashcat_flags 2>/dev/null || true)

benchmark_date=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

benchmarks_json=$(echo "$benchmark_output" | grep -v '^#' | grep -v '^$' | while IFS=: read -r dev_id _f1 hash_mode exec_ms _f2 speed; do
    exec_sec=$(echo "scale=1; $exec_ms / 1000" | bc)
    printf '{"hash_mode":%s,"hash_name":"mode_%s","speed":%s,"exec_runtime_ms":%s}\n' \
        "$hash_mode" "$hash_mode" "$speed" "$exec_sec"
done | jq -s '.')

jq -n \
    --arg hv "$HASHCAT_VERSION" \
    --arg gm "$gpu_name" \
    --arg ci "$CONTAINER_IMAGE" \
    --arg dv "$driver_version" \
    --arg cv "$CUDA_VERSION" \
    --arg km "$KERNEL_MODE" \
    --arg bd "$benchmark_date" \
    --argjson bm "$benchmarks_json" \
    '{
        hashcat_version: $hv,
        gpu_model: $gm,
        container_image: $ci,
        driver_version: $dv,
        cuda_version: $cv,
        kernel_mode: $km,
        benchmark_date: $bd,
        benchmarks: $bm
    }' | tee /tmp/result.json
```

- [ ] **Step 3: Add container commands to Justfile**

Append to `Justfile`:

```just
# Container registry
registry := "ghcr.io/YOUR_USERNAME/hashcat-bench"

# Build benchmark container image
build-image HASHCAT_VERSION:
    docker build \
        --build-arg HASHCAT_VERSION={{ HASHCAT_VERSION }} \
        -t {{ registry }}:{{ HASHCAT_VERSION }}-cuda12.2 \
        container/

# Push image to GHCR
push-image HASHCAT_VERSION:
    docker push {{ registry }}:{{ HASHCAT_VERSION }}-cuda12.2
```

- [ ] **Step 4: Verify Dockerfile syntax**

Run: `docker build --check container/` (or just verify the file is parseable)

If Docker is available, test with:
Run: `docker build --build-arg HASHCAT_VERSION=v6.2.6 -t hashcat-bench:test container/`
Expected: Image builds successfully (no GPU required for build)

---

## Task 6: Vast.ai Provider

**Files:**
- Create: `src/hashcat_bench/provider.py`
- Create: `tests/test_provider.py`

- [ ] **Step 1: Write provider tests**

Create `tests/test_provider.py`:

```python
from unittest.mock import MagicMock, patch
from hashcat_bench.provider import VastProvider


def _mock_vast():
    mock = MagicMock()
    return mock


def test_search_offers_calls_sdk():
    mock_sdk = _mock_vast()
    mock_sdk.search_offers.return_value = [
        {"id": 123, "gpu_name": "RTX_4090", "dph_total": 0.35, "num_gpus": 1, "reliability": 0.95, "cuda_max_good": 12.2},
        {"id": 456, "gpu_name": "RTX_4090", "dph_total": 0.50, "num_gpus": 1, "reliability": 0.80, "cuda_max_good": 12.2},
    ]
    provider = VastProvider(sdk=mock_sdk)
    offers = provider.search_gpu("RTX 4090")
    assert len(offers) == 2
    assert offers[0]["id"] == 123


def test_search_offers_filters_by_name():
    mock_sdk = _mock_vast()
    mock_sdk.search_offers.return_value = []
    provider = VastProvider(sdk=mock_sdk)
    provider.search_gpu("RTX 4090")
    mock_sdk.search_offers.assert_called_once()
    call_kwargs = mock_sdk.search_offers.call_args
    assert "RTX_4090" in str(call_kwargs) or "RTX 4090" in str(call_kwargs)


def test_cheapest_offer():
    mock_sdk = _mock_vast()
    mock_sdk.search_offers.return_value = [
        {"id": 456, "gpu_name": "RTX_4090", "dph_total": 0.50, "num_gpus": 1, "reliability": 0.95, "cuda_max_good": 12.2},
        {"id": 123, "gpu_name": "RTX_4090", "dph_total": 0.30, "num_gpus": 1, "reliability": 0.95, "cuda_max_good": 12.2},
    ]
    provider = VastProvider(sdk=mock_sdk)
    offer = provider.cheapest_offer("RTX 4090")
    assert offer["id"] == 123


def test_cheapest_offer_none_available():
    mock_sdk = _mock_vast()
    mock_sdk.search_offers.return_value = []
    provider = VastProvider(sdk=mock_sdk)
    offer = provider.cheapest_offer("RTX 4090")
    assert offer is None


def test_create_instance():
    mock_sdk = _mock_vast()
    mock_sdk.create_instance.return_value = {"new_contract": 789, "success": True}
    provider = VastProvider(sdk=mock_sdk)
    instance_id = provider.create_instance(
        offer_id=123,
        image="ghcr.io/user/hashcat-bench:v6.2.6-cuda12.2",
        env={"HASHCAT_VERSION": "v6.2.6", "KERNEL_MODE": "optimized"},
    )
    assert instance_id == 789


def test_destroy_instance():
    mock_sdk = _mock_vast()
    provider = VastProvider(sdk=mock_sdk)
    provider.destroy_instance(789)
    mock_sdk.destroy_instance.assert_called_once_with(id=789)


def test_instance_status():
    mock_sdk = _mock_vast()
    mock_sdk.show_instance.return_value = {"actual_status": "running", "ssh_host": "1.2.3.4", "ssh_port": 22}
    provider = VastProvider(sdk=mock_sdk)
    status = provider.instance_status(789)
    assert status["actual_status"] == "running"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `just test tests/test_provider.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'hashcat_bench.provider'`

- [ ] **Step 3: Implement provider**

Create `src/hashcat_bench/provider.py`:

```python
from __future__ import annotations

from typing import Any


class VastProvider:
    def __init__(self, sdk: Any = None, api_key: str | None = None):
        if sdk is not None:
            self._sdk = sdk
        else:
            from vastai import VastAI
            self._sdk = VastAI(api_key=api_key)

    def search_gpu(self, vastai_name: str) -> list[dict]:
        search_name = vastai_name.replace(" ", "_")
        offers = self._sdk.search_offers(
            query=f"gpu_name={search_name} num_gpus=1 rentable=true",
            order="dph_total",
            limit="20",
        )
        if offers is None:
            return []
        return offers

    def cheapest_offer(self, vastai_name: str, min_reliability: float = 0.8) -> dict | None:
        offers = self.search_gpu(vastai_name)
        viable = [o for o in offers if o.get("reliability", 0) >= min_reliability]
        if not viable:
            return None
        return min(viable, key=lambda o: o["dph_total"])

    def create_instance(self, offer_id: int, image: str, env: dict[str, str] | None = None) -> int:
        env_str = " ".join(f"-e {k}={v}" for k, v in (env or {}).items())
        result = self._sdk.create_instance(
            id=offer_id,
            image=image,
            disk=20,
            env=env_str,
        )
        return result["new_contract"]

    def instance_status(self, instance_id: int) -> dict:
        return self._sdk.show_instance(id=instance_id)

    def destroy_instance(self, instance_id: int) -> None:
        self._sdk.destroy_instance(id=instance_id)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `just test tests/test_provider.py -v`
Expected: All 7 tests PASS

---

## Task 7: Cost Estimator

**Files:**
- Create: `src/hashcat_bench/estimator.py`
- Create: `tests/test_estimator.py`

- [ ] **Step 1: Write estimator tests**

Create `tests/test_estimator.py`:

```python
from unittest.mock import MagicMock
from hashcat_bench.estimator import CostEstimator
from hashcat_bench.models import GpuModel


def _mock_provider(offers_by_gpu: dict[str, list[dict]]):
    provider = MagicMock()

    def search_side_effect(name):
        return offers_by_gpu.get(name, [])

    def cheapest_side_effect(name, min_reliability=0.8):
        results = offers_by_gpu.get(name, [])
        viable = [o for o in results if o.get("reliability", 0) >= min_reliability]
        return min(viable, key=lambda o: o["dph_total"]) if viable else None

    provider.search_gpu.side_effect = search_side_effect
    provider.cheapest_offer.side_effect = cheapest_side_effect
    return provider


def test_estimate_single():
    provider = _mock_provider({
        "RTX 4090": [{"id": 1, "dph_total": 0.40, "reliability": 0.95}],
    })
    estimator = CostEstimator(provider)
    est = estimator.estimate_single("RTX 4090", estimated_minutes=15)
    assert est.gpu_name == "RTX 4090"
    assert est.price_per_hour == 0.40
    assert est.estimated_minutes == 15
    assert 0.09 < est.estimated_cost < 0.12  # $0.40/hr * 0.25hr = $0.10, plus safety margin


def test_estimate_single_unavailable():
    provider = _mock_provider({})
    estimator = CostEstimator(provider)
    est = estimator.estimate_single("RTX 4090")
    assert est.available is False
    assert est.estimated_cost == 0.0


def test_estimate_matrix():
    provider = _mock_provider({
        "RTX 4090": [{"id": 1, "dph_total": 0.40, "reliability": 0.95}],
        "RTX 3080": [{"id": 2, "dph_total": 0.15, "reliability": 0.90}],
    })
    models = [
        GpuModel(name="RTX 4090", slug="rtx-4090", family="Ada Lovelace", vendor="nvidia", vastai_name="RTX 4090"),
        GpuModel(name="RTX 3080", slug="rtx-3080", family="Ampere", vendor="nvidia", vastai_name="RTX 3080"),
    ]
    estimator = CostEstimator(provider)
    estimates = estimator.estimate_matrix(models, skip_slugs=["rtx-3080"])
    assert len(estimates) == 2
    assert estimates[0].gpu_name == "RTX 4090"
    assert estimates[0].skipped is False
    assert estimates[1].gpu_name == "RTX 3080"
    assert estimates[1].skipped is True
    total = estimator.total_cost(estimates)
    assert total > 0


def test_total_cost_excludes_skipped():
    provider = _mock_provider({
        "RTX 4090": [{"id": 1, "dph_total": 0.40, "reliability": 0.95}],
    })
    models = [
        GpuModel(name="RTX 4090", slug="rtx-4090", family="Ada Lovelace", vendor="nvidia", vastai_name="RTX 4090"),
    ]
    estimator = CostEstimator(provider)
    estimates = estimator.estimate_matrix(models, skip_slugs=["rtx-4090"])
    total = estimator.total_cost(estimates)
    assert total == 0.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `just test tests/test_estimator.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'hashcat_bench.estimator'`

- [ ] **Step 3: Implement estimator**

Create `src/hashcat_bench/estimator.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from hashcat_bench.models import GpuModel
from hashcat_bench.provider import VastProvider

DEFAULT_RUNTIME_MINUTES = 15
SAFETY_MULTIPLIER = 1.5


@dataclass
class CostEstimate:
    gpu_name: str
    available: bool = True
    skipped: bool = False
    price_per_hour: float = 0.0
    estimated_minutes: float = 0.0
    estimated_cost: float = 0.0


class CostEstimator:
    def __init__(self, provider: VastProvider):
        self._provider = provider

    def estimate_single(
        self, vastai_name: str, estimated_minutes: float = DEFAULT_RUNTIME_MINUTES
    ) -> CostEstimate:
        offer = self._provider.cheapest_offer(vastai_name)
        if offer is None:
            return CostEstimate(gpu_name=vastai_name, available=False)

        price_per_hour = offer["dph_total"]
        hours = (estimated_minutes / 60.0) * SAFETY_MULTIPLIER
        cost = price_per_hour * hours

        return CostEstimate(
            gpu_name=vastai_name,
            available=True,
            price_per_hour=price_per_hour,
            estimated_minutes=estimated_minutes,
            estimated_cost=round(cost, 4),
        )

    def estimate_matrix(
        self,
        models: list[GpuModel],
        skip_slugs: list[str] | None = None,
    ) -> list[CostEstimate]:
        skip = set(skip_slugs or [])
        estimates = []
        for model in models:
            if model.slug in skip:
                estimates.append(CostEstimate(gpu_name=model.vastai_name, skipped=True))
            else:
                est = self.estimate_single(model.vastai_name)
                estimates.append(est)
        return estimates

    def total_cost(self, estimates: list[CostEstimate]) -> float:
        return sum(e.estimated_cost for e in estimates if not e.skipped)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `just test tests/test_estimator.py -v`
Expected: All 4 tests PASS

---

## Task 8: Benchmark Runner

**Files:**
- Create: `src/hashcat_bench/runner.py`
- Create: `tests/test_runner.py`

- [ ] **Step 1: Write runner tests**

Create `tests/test_runner.py`:

```python
import json
import time
from unittest.mock import MagicMock, patch, call

from hashcat_bench.runner import BenchmarkRunner


def _make_provider():
    provider = MagicMock()
    provider.cheapest_offer.return_value = {"id": 100, "dph_total": 0.35}
    provider.create_instance.return_value = 789
    provider.instance_status.side_effect = [
        {"actual_status": "loading"},
        {"actual_status": "running", "ssh_host": "1.2.3.4", "ssh_port": 22222},
    ]
    return provider


def test_run_calls_provider_lifecycle():
    provider = _make_provider()
    runner = BenchmarkRunner(provider=provider)

    sample_result = {
        "hashcat_version": "v6.2.6",
        "gpu_model": "RTX 4090",
        "container_image": "img",
        "driver_version": "535",
        "cuda_version": "12.2",
        "kernel_mode": "optimized",
        "benchmark_date": "2026-01-01T00:00:00Z",
        "benchmarks": [],
    }

    with patch.object(runner, "_collect_results", return_value=json.dumps(sample_result)):
        with patch("hashcat_bench.runner.time") as mock_time:
            mock_time.sleep = MagicMock()
            mock_time.time = MagicMock(side_effect=[0, 10, 20, 30])
            result = runner.run(
                vastai_name="RTX 4090",
                image="ghcr.io/user/hashcat-bench:v6.2.6-cuda12.2",
                hashcat_version="v6.2.6",
                kernel_mode="optimized",
            )

    provider.cheapest_offer.assert_called_once_with("RTX 4090")
    provider.create_instance.assert_called_once()
    provider.destroy_instance.assert_called_once_with(789)
    assert result.hashcat_version == "v6.2.6"


def test_run_no_offers_raises():
    provider = MagicMock()
    provider.cheapest_offer.return_value = None
    runner = BenchmarkRunner(provider=provider)

    try:
        runner.run(
            vastai_name="RTX 9999",
            image="img",
            hashcat_version="v6.2.6",
            kernel_mode="optimized",
        )
        assert False, "Should have raised"
    except RuntimeError as e:
        assert "No available offers" in str(e)


def test_run_destroys_on_failure():
    provider = MagicMock()
    provider.cheapest_offer.return_value = {"id": 100, "dph_total": 0.35}
    provider.create_instance.return_value = 789
    provider.instance_status.side_effect = Exception("API error")

    runner = BenchmarkRunner(provider=provider)
    try:
        with patch("hashcat_bench.runner.time") as mock_time:
            mock_time.sleep = MagicMock()
            mock_time.time = MagicMock(return_value=0)
            runner.run(
                vastai_name="RTX 4090",
                image="img",
                hashcat_version="v6.2.6",
                kernel_mode="optimized",
            )
        assert False, "Should have raised"
    except Exception:
        pass

    provider.destroy_instance.assert_called_once_with(789)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `just test tests/test_runner.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'hashcat_bench.runner'`

- [ ] **Step 3: Implement runner**

Create `src/hashcat_bench/runner.py`:

```python
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
        cuda_version: str = "12.2",
    ) -> BenchmarkResult:
        offer = self._provider.cheapest_offer(vastai_name)
        if offer is None:
            raise RuntimeError(f"No available offers for GPU: {vastai_name}")

        env = {
            "HASHCAT_VERSION": hashcat_version,
            "KERNEL_MODE": kernel_mode,
            "CUDA_VERSION": cuda_version,
            "CONTAINER_IMAGE": image,
        }

        instance_id = self._provider.create_instance(
            offer_id=offer["id"],
            image=image,
            env=env,
        )

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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `just test tests/test_runner.py -v`
Expected: All 3 tests PASS

---

## Task 9: CLI Entrypoint

**Files:**
- Create: `src/hashcat_bench/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write CLI tests**

Create `tests/test_cli.py`:

```python
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from hashcat_bench.cli import build_index_cmd, status_cmd


def test_build_index_cmd(tmp_path):
    results_dir = tmp_path / "results" / "v6.2.6"
    results_dir.mkdir(parents=True)
    (results_dir / "rtx-4090.json").write_text(json.dumps({
        "hashcat_version": "v6.2.6",
        "gpu_model": "RTX 4090",
        "container_image": "img",
        "driver_version": "535",
        "cuda_version": "12.2",
        "kernel_mode": "optimized",
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `just test tests/test_cli.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'hashcat_bench.cli'`

- [ ] **Step 3: Implement CLI**

Create `src/hashcat_bench/cli.py`:

```python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from hashcat_bench.data import DataManager
from hashcat_bench.models import GpuModelRegistry


def build_index_cmd(data_dir: Path) -> None:
    dm = DataManager(data_dir)
    index = dm.build_index()
    count = len(index["results"])
    print(f"Built index.json: {count} result(s), {len(index['versions'])} version(s), {len(index['gpu_models'])} GPU(s)")


def status_cmd(data_dir: Path, versions: list[str]) -> None:
    dm = DataManager(data_dir)
    gpu_file = data_dir / "gpu-models.json"
    if not gpu_file.exists():
        print("Error: gpu-models.json not found", file=sys.stderr)
        sys.exit(1)

    registry = GpuModelRegistry.load(gpu_file)
    slugs = [m.slug for m in registry.models]

    for version in versions:
        print(f"\n=== {version} ===")
        for slug in slugs:
            path = data_dir / "results" / version / f"{slug}.json"
            marker = "OK" if path.exists() else "MISSING"
            print(f"  {slug:20s} [{marker}]")


def list_gpus_cmd(filter_str: str | None = None) -> None:
    from hashcat_bench.provider import VastProvider

    provider = VastProvider()
    gpu_names = [
        "RTX 5090", "RTX 5080", "RTX 5070 Ti", "RTX 5070",
        "RTX 4090", "RTX 4080", "RTX 4070 Ti", "RTX 4070", "RTX 4060 Ti", "RTX 4060",
        "RTX 3090", "RTX 3080", "RTX 3070", "RTX 3060",
    ]

    if filter_str:
        gpu_names = [g for g in gpu_names if filter_str.lower() in g.lower()]

    print(f"{'GPU':20s} {'Available':>10s} {'$/hr':>10s}")
    print("-" * 42)
    for name in gpu_names:
        offers = provider.search_gpu(name)
        if offers:
            cheapest = min(offers, key=lambda o: o["dph_total"])
            print(f"{name:20s} {len(offers):>10d} ${cheapest['dph_total']:>9.3f}")
        else:
            print(f"{name:20s} {'none':>10s} {'n/a':>10s}")


def estimate_cmd(data_dir: Path, gpu_slug: str, hashcat_version: str) -> None:
    from hashcat_bench.estimator import CostEstimator
    from hashcat_bench.provider import VastProvider

    gpu_file = data_dir / "gpu-models.json"
    registry = GpuModelRegistry.load(gpu_file)
    model = registry.get_by_slug(gpu_slug)
    if model is None:
        print(f"Error: unknown GPU slug '{gpu_slug}'", file=sys.stderr)
        sys.exit(1)

    dm = DataManager(data_dir)
    already_exists = dm.result_exists(hashcat_version, gpu_slug, "optimized")

    provider = VastProvider()
    estimator = CostEstimator(provider)
    est = estimator.estimate_single(model.vastai_name)

    status = "skip (already exists)" if already_exists else "will run"
    if est.available:
        print(f"{model.name}: ${est.price_per_hour:.3f}/hr × ~{est.estimated_minutes:.0f}min = ~${est.estimated_cost:.3f} | {status}")
    else:
        print(f"{model.name}: not available on Vast.ai | {status}")


def estimate_matrix_cmd(data_dir: Path, hashcat_version: str) -> None:
    from hashcat_bench.estimator import CostEstimator
    from hashcat_bench.provider import VastProvider

    gpu_file = data_dir / "gpu-models.json"
    registry = GpuModelRegistry.load(gpu_file)
    dm = DataManager(data_dir)
    skip_slugs = [m.slug for m in registry.models if dm.result_exists(hashcat_version, m.slug, "optimized")]

    provider = VastProvider()
    estimator = CostEstimator(provider)
    estimates = estimator.estimate_matrix(registry.models, skip_slugs=skip_slugs)

    will_run = 0
    for est, model in zip(estimates, registry.models):
        if est.skipped:
            print(f"  {model.name:20s}  skip (already exists)")
        elif est.available:
            print(f"  {model.name:20s}  ${est.estimated_cost:.3f} est.")
            will_run += 1
        else:
            print(f"  {model.name:20s}  not available")

    total = estimator.total_cost(estimates)
    skipped = sum(1 for e in estimates if e.skipped)
    print(f"\n  Total: ${total:.2f} est. for {will_run} run(s) ({skipped} skipped)")


def bench_cmd(data_dir: Path, gpu_slug: str, hashcat_version: str, kernel_mode: str = "optimized") -> None:
    from hashcat_bench.provider import VastProvider
    from hashcat_bench.runner import BenchmarkRunner

    gpu_file = data_dir / "gpu-models.json"
    registry = GpuModelRegistry.load(gpu_file)
    model = registry.get_by_slug(gpu_slug)
    if model is None:
        print(f"Error: unknown GPU slug '{gpu_slug}'", file=sys.stderr)
        sys.exit(1)

    dm = DataManager(data_dir)
    file_slug = gpu_slug if kernel_mode == "optimized" else f"{gpu_slug}-default"
    if dm.result_exists(hashcat_version, file_slug, kernel_mode):
        print(f"Already benchmarked: {model.name} @ {hashcat_version} ({kernel_mode})")
        return

    image = f"ghcr.io/YOUR_USERNAME/hashcat-bench:{hashcat_version}-cuda12.2"
    provider = VastProvider()
    runner = BenchmarkRunner(provider=provider)

    print(f"Benchmarking {model.name} @ {hashcat_version} ({kernel_mode})...")
    result = runner.run(
        vastai_name=model.vastai_name,
        image=image,
        hashcat_version=hashcat_version,
        kernel_mode=kernel_mode,
    )

    path = dm.save_result(result)
    print(f"Result saved to {path}")


def bench_matrix_cmd(
    data_dir: Path,
    hashcat_version: str,
    kernel_mode: str = "optimized",
    budget_cap: float | None = None,
) -> None:
    from hashcat_bench.estimator import CostEstimator
    from hashcat_bench.provider import VastProvider

    gpu_file = data_dir / "gpu-models.json"
    registry = GpuModelRegistry.load(gpu_file)

    dm = DataManager(data_dir)
    missing_slugs = dm.list_missing(hashcat_version, [m.slug for m in registry.models], kernel_mode)

    if not missing_slugs:
        print("All GPUs already benchmarked for this version.")
        return

    if budget_cap is not None:
        provider = VastProvider()
        estimator = CostEstimator(provider)
        missing_models = [m for m in registry.models if m.slug in missing_slugs]
        estimates = estimator.estimate_matrix(missing_models)
        total = estimator.total_cost(estimates)
        if total > budget_cap:
            print(f"Estimated cost ${total:.2f} exceeds budget cap ${budget_cap:.2f}. Aborting.")
            return

    for slug in missing_slugs:
        print(f"\n--- {slug} ---")
        bench_cmd(data_dir, slug, hashcat_version, kernel_mode)


def main() -> None:
    parser = argparse.ArgumentParser(prog="hashcat-bench", description="Hashcat GPU benchmark orchestrator")
    parser.add_argument("--data-dir", type=Path, default=Path("data"), help="Data directory")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("build-index", help="Build data/index.json from results")

    p_status = sub.add_parser("status", help="Show benchmark status")
    p_status.add_argument("--versions", nargs="+", required=True, help="Hashcat versions to check")

    p_list = sub.add_parser("list-gpus", help="List available GPUs on Vast.ai")
    p_list.add_argument("--filter", dest="filter_str", help="Filter by name")

    p_est = sub.add_parser("estimate", help="Estimate cost for a single benchmark")
    p_est.add_argument("--gpu", required=True, help="GPU slug")
    p_est.add_argument("--hashcat", required=True, help="Hashcat version")

    p_estm = sub.add_parser("estimate-matrix", help="Estimate cost for full GPU matrix")
    p_estm.add_argument("--hashcat", required=True, help="Hashcat version")

    p_bench = sub.add_parser("bench", help="Run a single benchmark")
    p_bench.add_argument("--gpu", required=True, help="GPU slug")
    p_bench.add_argument("--hashcat", required=True, help="Hashcat version")
    p_bench.add_argument("--kernel-mode", default="optimized", choices=["optimized", "default"])

    p_bm = sub.add_parser("bench-matrix", help="Run benchmarks for all GPUs")
    p_bm.add_argument("--hashcat", required=True, help="Hashcat version")
    p_bm.add_argument("--kernel-mode", default="optimized", choices=["optimized", "default"])
    p_bm.add_argument("--budget-cap", type=float, help="Max $ to spend")

    args = parser.parse_args()

    if args.command == "build-index":
        build_index_cmd(args.data_dir)
    elif args.command == "status":
        status_cmd(args.data_dir, args.versions)
    elif args.command == "list-gpus":
        list_gpus_cmd(args.filter_str)
    elif args.command == "estimate":
        estimate_cmd(args.data_dir, args.gpu, args.hashcat)
    elif args.command == "estimate-matrix":
        estimate_matrix_cmd(args.data_dir, args.hashcat)
    elif args.command == "bench":
        bench_cmd(args.data_dir, args.gpu, args.hashcat, args.kernel_mode)
    elif args.command == "bench-matrix":
        bench_matrix_cmd(args.data_dir, args.hashcat, args.kernel_mode, args.budget_cap)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `just test tests/test_cli.py -v`
Expected: All 2 tests PASS

---

## Task 10: Complete Justfile

**Files:**
- Modify: `Justfile`

- [ ] **Step 1: Replace Justfile with complete version**

```just
set dotenv-load

python := "uv run"
data_dir := "data"

# --- Setup ---

setup:
    uv sync --all-extras
    cd site && npm install

# --- Tests ---

test *ARGS:
    {{ python }} pytest tests/ {{ ARGS }}

test-cov:
    {{ python }} pytest tests/ --cov=hashcat_bench --cov-report=term-missing

# --- Discovery ---

list-gpus *FILTER:
    {{ python }} hashcat-bench list-gpus {{ if FILTER != "" { "--filter " + FILTER } else { "" } }}

# --- Cost Estimation ---

estimate GPU HASHCAT:
    {{ python }} hashcat-bench --data-dir {{ data_dir }} estimate --gpu {{ GPU }} --hashcat {{ HASHCAT }}

estimate-matrix HASHCAT:
    {{ python }} hashcat-bench --data-dir {{ data_dir }} estimate-matrix --hashcat {{ HASHCAT }}

# --- Container ---

registry := env("HASHCAT_BENCH_REGISTRY", "ghcr.io/YOUR_USERNAME/hashcat-bench")

build-image HASHCAT_VERSION:
    docker build \
        --build-arg HASHCAT_VERSION={{ HASHCAT_VERSION }} \
        -t {{ registry }}:{{ HASHCAT_VERSION }}-cuda12.2 \
        container/

push-image HASHCAT_VERSION:
    docker push {{ registry }}:{{ HASHCAT_VERSION }}-cuda12.2

# --- Benchmarking ---

bench GPU HASHCAT:
    {{ python }} hashcat-bench --data-dir {{ data_dir }} bench --gpu {{ GPU }} --hashcat {{ HASHCAT }}

bench-matrix HASHCAT:
    {{ python }} hashcat-bench --data-dir {{ data_dir }} bench-matrix --hashcat {{ HASHCAT }}

bench-matrix-capped HASHCAT BUDGET:
    {{ python }} hashcat-bench --data-dir {{ data_dir }} bench-matrix --hashcat {{ HASHCAT }} --budget-cap {{ BUDGET }}

# --- Data ---

build-index:
    {{ python }} hashcat-bench --data-dir {{ data_dir }} build-index

validate:
    {{ python }} -c "from hashcat_bench.data import DataManager; from pathlib import Path; dm = DataManager(Path('{{ data_dir }}')); [print(f'OK: {r.hashcat_version}/{r.gpu_model}') for r in dm.load_all_results()]"

status HASHCAT:
    {{ python }} hashcat-bench --data-dir {{ data_dir }} status --versions {{ HASHCAT }}

# --- Frontend ---

dev:
    cd site && npm run dev

build-site: build-index
    cp {{ data_dir }}/index.json site/public/index.json
    cd site && npm run build
```

- [ ] **Step 2: Verify Justfile syntax**

Run: `just --list`
Expected: All commands listed without errors

---

## Task 11: Svelte Frontend Scaffolding

**Files:**
- Create: `site/` directory via `npm create vite`
- Create: `site/public/index.json` (sample data)

- [ ] **Step 1: Initialize Svelte project**

Run: `cd site && npm create vite@latest . -- --template svelte && npm install`

If the `site/` directory doesn't exist yet, create it first: `mkdir -p site`

Expected: Svelte project scaffolded with Vite

- [ ] **Step 2: Install Chart.js**

Run: `cd site && npm install chart.js`

- [ ] **Step 3: Create sample index.json for development**

Create `site/public/index.json`:

```json
{
  "generated_at": "2026-04-25T15:00:00Z",
  "versions": ["v6.2.6", "v6.2.5"],
  "gpu_models": ["RTX 4090", "RTX 3080"],
  "hash_modes": [
    {"mode": 0, "name": "MD5"},
    {"mode": 100, "name": "SHA1"},
    {"mode": 1400, "name": "SHA2-256"},
    {"mode": 1700, "name": "SHA2-512"},
    {"mode": 3000, "name": "LM"},
    {"mode": 5600, "name": "NetNTLMv2"},
    {"mode": 13100, "name": "Kerberos 5, etype 23, TGS-REP"},
    {"mode": 22000, "name": "WPA-PBKDF2-PMKID+EAPOL"}
  ],
  "results": [
    {
      "hashcat_version": "v6.2.6",
      "gpu_model": "RTX 4090",
      "driver_version": "535.129.03",
      "cuda_version": "12.2",
      "kernel_mode": "optimized",
      "benchmark_date": "2026-04-25T14:30:00Z",
      "benchmarks": [
        {"hash_mode": 0, "speed": 164000000000, "exec_runtime_ms": 12.5},
        {"hash_mode": 100, "speed": 56000000000, "exec_runtime_ms": 18.2},
        {"hash_mode": 1400, "speed": 22100000000, "exec_runtime_ms": 22.1},
        {"hash_mode": 1700, "speed": 8050000000, "exec_runtime_ms": 35.6},
        {"hash_mode": 3000, "speed": 98000000000, "exec_runtime_ms": 8.5},
        {"hash_mode": 5600, "speed": 8800000000, "exec_runtime_ms": 31.0},
        {"hash_mode": 13100, "speed": 1650000000, "exec_runtime_ms": 85.0},
        {"hash_mode": 22000, "speed": 1200000, "exec_runtime_ms": 142.0}
      ]
    },
    {
      "hashcat_version": "v6.2.6",
      "gpu_model": "RTX 3080",
      "driver_version": "525.85.12",
      "cuda_version": "12.2",
      "kernel_mode": "optimized",
      "benchmark_date": "2026-04-25T15:00:00Z",
      "benchmarks": [
        {"hash_mode": 0, "speed": 82100000000, "exec_runtime_ms": 25.0},
        {"hash_mode": 100, "speed": 28300000000, "exec_runtime_ms": 36.0},
        {"hash_mode": 1400, "speed": 11200000000, "exec_runtime_ms": 44.0},
        {"hash_mode": 1700, "speed": 4020000000, "exec_runtime_ms": 71.0},
        {"hash_mode": 3000, "speed": 49000000000, "exec_runtime_ms": 17.0},
        {"hash_mode": 5600, "speed": 4400000000, "exec_runtime_ms": 62.0},
        {"hash_mode": 13100, "speed": 825000000, "exec_runtime_ms": 170.0},
        {"hash_mode": 22000, "speed": 600000, "exec_runtime_ms": 284.0}
      ]
    },
    {
      "hashcat_version": "v6.2.5",
      "gpu_model": "RTX 4090",
      "driver_version": "530.41.03",
      "cuda_version": "12.1",
      "kernel_mode": "optimized",
      "benchmark_date": "2026-03-15T10:00:00Z",
      "benchmarks": [
        {"hash_mode": 0, "speed": 161000000000, "exec_runtime_ms": 13.0},
        {"hash_mode": 100, "speed": 55000000000, "exec_runtime_ms": 19.0},
        {"hash_mode": 1400, "speed": 21800000000, "exec_runtime_ms": 23.0},
        {"hash_mode": 1700, "speed": 7900000000, "exec_runtime_ms": 36.0},
        {"hash_mode": 3000, "speed": 96000000000, "exec_runtime_ms": 9.0},
        {"hash_mode": 5600, "speed": 8600000000, "exec_runtime_ms": 32.0},
        {"hash_mode": 13100, "speed": 1620000000, "exec_runtime_ms": 87.0},
        {"hash_mode": 22000, "speed": 1180000, "exec_runtime_ms": 145.0}
      ]
    }
  ]
}
```

- [ ] **Step 4: Verify dev server starts**

Run: `just dev`
Expected: Vite dev server starts at `http://localhost:5173`

---

## Task 12: Frontend — Data Layer & Filter Bar

**Files:**
- Create: `site/src/lib/data.js`
- Create: `site/src/lib/format.js`
- Create: `site/src/lib/FilterBar.svelte`
- Modify: `site/src/App.svelte`

- [ ] **Step 1: Create data loading and formatting utilities**

Create `site/src/lib/data.js`:

```javascript
export async function loadIndex() {
  const res = await fetch('./index.json');
  return res.json();
}

export function filterResults(index, { version, gpuModels, hashModeQuery }) {
  let results = index.results;

  if (version) {
    results = results.filter(r => r.hashcat_version === version);
  }

  if (gpuModels && gpuModels.length > 0) {
    results = results.filter(r => gpuModels.includes(r.gpu_model));
  }

  let hashModes = index.hash_modes;
  if (hashModeQuery) {
    const q = hashModeQuery.toLowerCase();
    hashModes = hashModes.filter(
      m => m.name.toLowerCase().includes(q) || String(m.mode).includes(q)
    );
  }

  return { results, hashModes };
}
```

Create `site/src/lib/format.js`:

```javascript
export function formatSpeed(hashesPerSecond) {
  if (hashesPerSecond >= 1e12) return (hashesPerSecond / 1e12).toFixed(1) + ' TH/s';
  if (hashesPerSecond >= 1e9) return (hashesPerSecond / 1e9).toFixed(1) + ' GH/s';
  if (hashesPerSecond >= 1e6) return (hashesPerSecond / 1e6).toFixed(1) + ' MH/s';
  if (hashesPerSecond >= 1e3) return (hashesPerSecond / 1e3).toFixed(1) + ' kH/s';
  return hashesPerSecond + ' H/s';
}
```

- [ ] **Step 2: Create FilterBar component**

Create `site/src/lib/FilterBar.svelte`:

```svelte
<script>
  let { versions = [], gpuModels = [], selectedVersion = $bindable(''), selectedGpus = $bindable([]), hashModeQuery = $bindable('') } = $props();

  function toggleGpu(gpu) {
    if (selectedGpus.includes(gpu)) {
      selectedGpus = selectedGpus.filter(g => g !== gpu);
    } else {
      selectedGpus = [...selectedGpus, gpu];
    }
  }
</script>

<div class="filter-bar">
  <div class="filter-group">
    <label for="version-select">Hashcat Version</label>
    <select id="version-select" bind:value={selectedVersion}>
      {#each versions as v}
        <option value={v}>{v}</option>
      {/each}
    </select>
  </div>

  <div class="filter-group">
    <label>GPU Models</label>
    <div class="gpu-chips">
      {#each gpuModels as gpu}
        <button
          class="chip"
          class:active={selectedGpus.includes(gpu)}
          onclick={() => toggleGpu(gpu)}
        >
          {gpu}
        </button>
      {/each}
    </div>
  </div>

  <div class="filter-group">
    <label for="hash-search">Hash Mode</label>
    <input
      id="hash-search"
      type="text"
      placeholder="Search by name or mode number..."
      bind:value={hashModeQuery}
    />
  </div>
</div>
```

- [ ] **Step 3: Wire up App.svelte**

Replace `site/src/App.svelte`:

```svelte
<script>
  import { onMount } from 'svelte';
  import { loadIndex, filterResults } from './lib/data.js';
  import FilterBar from './lib/FilterBar.svelte';

  let index = $state(null);
  let selectedVersion = $state('');
  let selectedGpus = $state([]);
  let hashModeQuery = $state('');
  let activeTab = $state('table');

  onMount(async () => {
    index = await loadIndex();
    if (index.versions.length > 0) {
      selectedVersion = index.versions[0];
    }
    if (index.gpu_models.length > 0) {
      selectedGpus = [...index.gpu_models];
    }
  });

  let filtered = $derived(
    index ? filterResults(index, { version: selectedVersion, gpuModels: selectedGpus, hashModeQuery }) : { results: [], hashModes: [] }
  );
</script>

<main>
  <header>
    <h1>Hashcat GPU Benchmarks</h1>
    <p>Standardized speed benchmarks across GPU models and hashcat versions</p>
    <nav>
      <a href="https://github.com/YOUR_USERNAME/hashcat-benchmarks" target="_blank">GitHub</a>
    </nav>
  </header>

  {#if index}
    <FilterBar
      versions={index.versions}
      gpuModels={index.gpu_models}
      bind:selectedVersion
      bind:selectedGpus
      bind:hashModeQuery
    />

    <div class="tabs">
      <button class:active={activeTab === 'table'} onclick={() => activeTab = 'table'}>Table</button>
      <button class:active={activeTab === 'compare'} onclick={() => activeTab = 'compare'}>Compare</button>
    </div>

    <div class="tab-content">
      {#if activeTab === 'table'}
        <p>Table view — Task 13</p>
      {:else}
        <p>Compare view — Task 14</p>
      {/if}
    </div>
  {:else}
    <p>Loading benchmark data...</p>
  {/if}
</main>
```

- [ ] **Step 4: Verify in browser**

Run: `just dev`
Open `http://localhost:5173`
Expected: Page loads, filter bar shows version dropdown, GPU chips, and hash mode search. Tabs show placeholder text.

---

## Task 13: Frontend — Table View

**Files:**
- Create: `site/src/lib/TableView.svelte`
- Modify: `site/src/App.svelte` (replace placeholder)

- [ ] **Step 1: Create TableView component**

Create `site/src/lib/TableView.svelte`:

```svelte
<script>
  import { formatSpeed } from './format.js';

  let { results = [], hashModes = [], selectedGpus = [] } = $props();

  let sortColumn = $state('mode');
  let sortAsc = $state(true);

  function speedForGpu(gpuModel, hashMode) {
    const result = results.find(r => r.gpu_model === gpuModel);
    if (!result) return null;
    const bench = result.benchmarks.find(b => b.hash_mode === hashMode);
    return bench ? bench.speed : null;
  }

  function toggleSort(col) {
    if (sortColumn === col) {
      sortAsc = !sortAsc;
    } else {
      sortColumn = col;
      sortAsc = col === 'mode';
    }
  }

  let sortedHashModes = $derived(() => {
    const modes = [...hashModes];
    if (sortColumn === 'mode') {
      modes.sort((a, b) => sortAsc ? a.mode - b.mode : b.mode - a.mode);
    } else if (sortColumn === 'name') {
      modes.sort((a, b) => sortAsc ? a.name.localeCompare(b.name) : b.name.localeCompare(a.name));
    } else {
      const gpu = sortColumn;
      modes.sort((a, b) => {
        const sa = speedForGpu(gpu, a.mode) ?? 0;
        const sb = speedForGpu(gpu, b.mode) ?? 0;
        return sortAsc ? sa - sb : sb - sa;
      });
    }
    return modes;
  });

  function sortIndicator(col) {
    if (sortColumn !== col) return '';
    return sortAsc ? ' ▲' : ' ▼';
  }
</script>

<div class="table-container">
  <table>
    <thead>
      <tr>
        <th class="sortable" onclick={() => toggleSort('mode')}>Mode{sortIndicator('mode')}</th>
        <th class="sortable" onclick={() => toggleSort('name')}>Hash Type{sortIndicator('name')}</th>
        {#each selectedGpus as gpu}
          <th class="sortable speed-col" onclick={() => toggleSort(gpu)}>{gpu}{sortIndicator(gpu)}</th>
        {/each}
      </tr>
    </thead>
    <tbody>
      {#each sortedHashModes() as hm}
        <tr>
          <td class="mode-col">{hm.mode}</td>
          <td>{hm.name}</td>
          {#each selectedGpus as gpu}
            {@const speed = speedForGpu(gpu, hm.mode)}
            <td class="speed-col" title={speed ? speed.toLocaleString() + ' H/s' : 'N/A'}>
              {speed ? formatSpeed(speed) : '—'}
            </td>
          {/each}
        </tr>
      {/each}
    </tbody>
  </table>
</div>
```

- [ ] **Step 2: Wire TableView into App.svelte**

In `site/src/App.svelte`, replace the table placeholder:

```svelte
{#if activeTab === 'table'}
  <TableView results={filtered.results} hashModes={filtered.hashModes} {selectedGpus} />
```

Add the import at the top of the `<script>` block:

```javascript
import TableView from './lib/TableView.svelte';
```

- [ ] **Step 3: Verify in browser**

Run: `just dev`
Expected: Table shows hash modes as rows, GPU names as columns, speeds formatted as GH/s etc. Clicking headers sorts. Hover shows raw H/s values.

---

## Task 14: Frontend — Compare View

**Files:**
- Create: `site/src/lib/CompareView.svelte`
- Modify: `site/src/App.svelte` (replace placeholder)

- [ ] **Step 1: Create CompareView component**

Create `site/src/lib/CompareView.svelte`:

```svelte
<script>
  import { onMount } from 'svelte';
  import { formatSpeed } from './format.js';
  import { Chart, BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js';

  Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend);

  let { results = [], hashModes = [], selectedGpus = [] } = $props();

  let selectedHashMode = $state(null);
  let canvas = $state();
  let chart = $state(null);

  $effect(() => {
    if (hashModes.length > 0 && selectedHashMode === null) {
      selectedHashMode = hashModes[0].mode;
    }
  });

  const GPU_COLORS = [
    '#6366f1', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6',
    '#ec4899', '#14b8a6', '#f97316', '#06b6d4', '#84cc16',
  ];

  function speedForGpu(gpuModel, hashMode) {
    const result = results.find(r => r.gpu_model === gpuModel);
    if (!result) return 0;
    const bench = result.benchmarks.find(b => b.hash_mode === hashMode);
    return bench ? bench.speed : 0;
  }

  $effect(() => {
    if (!canvas || selectedHashMode === null || selectedGpus.length === 0) return;

    const speeds = selectedGpus.map(gpu => speedForGpu(gpu, selectedHashMode));

    if (chart) chart.destroy();

    chart = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: selectedGpus,
        datasets: [{
          data: speeds,
          backgroundColor: selectedGpus.map((_, i) => GPU_COLORS[i % GPU_COLORS.length]),
          borderRadius: 4,
        }],
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => formatSpeed(ctx.raw),
            },
          },
        },
        scales: {
          x: {
            ticks: {
              callback: (val) => formatSpeed(val),
            },
          },
        },
      },
    });
  });

  let comparison = $derived(() => {
    if (selectedGpus.length < 2 || selectedHashMode === null) return null;
    const speeds = selectedGpus.map(gpu => ({ gpu, speed: speedForGpu(gpu, selectedHashMode) }));
    speeds.sort((a, b) => b.speed - a.speed);
    const fastest = speeds[0];
    const slowest = speeds[speeds.length - 1];
    if (slowest.speed === 0) return null;
    const ratio = fastest.speed / slowest.speed;
    return `${fastest.gpu} is ${ratio.toFixed(1)}× faster than ${slowest.gpu}`;
  });
</script>

<div class="compare-view">
  <div class="hash-mode-select">
    <label for="compare-hash-mode">Hash Mode</label>
    <select id="compare-hash-mode" bind:value={selectedHashMode}>
      {#each hashModes as hm}
        <option value={hm.mode}>{hm.mode} — {hm.name}</option>
      {/each}
    </select>
  </div>

  <div class="chart-container" style="height: {Math.max(200, selectedGpus.length * 50)}px;">
    <canvas bind:this={canvas}></canvas>
  </div>

  {#if comparison()}
    <p class="comparison-text">{comparison()}</p>
  {/if}
</div>
```

- [ ] **Step 2: Wire CompareView into App.svelte**

In `site/src/App.svelte`, replace the compare placeholder:

```svelte
{:else}
  <CompareView results={filtered.results} hashModes={filtered.hashModes} {selectedGpus} />
{/if}
```

Add the import:

```javascript
import CompareView from './lib/CompareView.svelte';
```

- [ ] **Step 3: Verify in browser**

Run: `just dev`
Expected: Compare tab shows hash mode dropdown, horizontal bar chart with GPU bars, and "RTX 4090 is 2.0× faster than RTX 3080" text below the chart.

---

## Task 15: Frontend — Export & Styling

**Files:**
- Create: `site/src/lib/ExportButton.svelte`
- Modify: `site/src/App.svelte` (add export button)
- Create: `site/src/app.css` (complete stylesheet)

- [ ] **Step 1: Create ExportButton component**

Create `site/src/lib/ExportButton.svelte`:

```svelte
<script>
  let { results = [], hashModes = [], selectedGpus = [] } = $props();

  function exportCSV() {
    const gpus = selectedGpus;
    let csv = 'Hash Mode,Hash Type,' + gpus.join(',') + '\n';

    for (const hm of hashModes) {
      const row = [hm.mode, `"${hm.name}"`];
      for (const gpu of gpus) {
        const result = results.find(r => r.gpu_model === gpu);
        const bench = result?.benchmarks.find(b => b.hash_mode === hm.mode);
        row.push(bench ? bench.speed : '');
      }
      csv += row.join(',') + '\n';
    }

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'hashcat-benchmarks.csv';
    a.click();
    URL.revokeObjectURL(url);
  }

  function exportJSON() {
    const data = { results, hashModes };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'hashcat-benchmarks.json';
    a.click();
    URL.revokeObjectURL(url);
  }
</script>

<div class="export-buttons">
  <button onclick={exportCSV}>Export CSV</button>
  <button onclick={exportJSON}>Export JSON</button>
</div>
```

- [ ] **Step 2: Add ExportButton to App.svelte filter bar area**

Add the import and place `<ExportButton>` after the FilterBar component:

```svelte
<ExportButton results={filtered.results} hashModes={filtered.hashModes} {selectedGpus} />
```

```javascript
import ExportButton from './lib/ExportButton.svelte';
```

- [ ] **Step 3: Create complete stylesheet**

Create `site/src/app.css` with styling for all components: dark theme, filter bar layout, table styles, chip buttons, chart container, tab bar, and export buttons. Import it in `site/src/main.js`:

```javascript
import './app.css';
import App from './App.svelte';
import { mount } from 'svelte';

const app = mount(App, { target: document.getElementById('app') });
export default app;
```

The CSS should cover:
- Dark background (`#0f172a`), light text
- Filter bar as a flex row with wrapping
- GPU chips as toggle buttons (active = highlighted)
- Table with alternating row colors, sticky header, horizontal scroll
- Speed columns right-aligned
- Tab bar styled as pill buttons
- Chart container with proper height
- Export buttons grouped inline
- Responsive layout for smaller screens

- [ ] **Step 4: Verify complete frontend in browser**

Run: `just dev`
Expected: Full dashboard with dark theme, working filters, table view with sorting, compare view with chart, and export buttons that download CSV/JSON files.

---

## Task 16: GitHub Actions Deploy Workflow

**Files:**
- Create: `.github/workflows/deploy.yml`

- [ ] **Step 1: Create deploy workflow**

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: npm
          cache-dependency-path: site/package-lock.json

      - name: Install Python dependencies
        run: uv sync

      - name: Build index
        run: uv run hashcat-bench --data-dir data build-index

      - name: Copy index to site
        run: cp data/index.json site/public/index.json

      - name: Install site dependencies
        run: cd site && npm ci

      - name: Build site
        run: cd site && npm run build

      - uses: actions/upload-pages-artifact@v3
        with:
          path: site/dist

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/deploy-pages@v4
        id: deployment
```

- [ ] **Step 2: Verify workflow syntax**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/deploy.yml'))" 2>/dev/null || echo "Install pyyaml or manually verify YAML syntax"`

Or just visually verify the YAML structure is correct.

---

## Task 17: Full Integration Verification

**Files:** None (verification only)

- [ ] **Step 1: Run full test suite**

Run: `just test -v`
Expected: All tests pass (models, parser, data, provider, estimator, runner, cli)

- [ ] **Step 2: Build the index from sample data**

If no real results exist yet, create a sample result file and test the pipeline:

Run: `just build-index`
Expected: Prints "Built index.json: N result(s)..." and creates `data/index.json`

- [ ] **Step 3: Build the site**

Run: `just build-site`
Expected: Site builds successfully in `site/dist/`

- [ ] **Step 4: Preview the built site**

Run: `cd site && npx serve dist`
Open `http://localhost:3000`
Expected: Production build renders correctly with all features working.

- [ ] **Step 5: Verify Justfile commands**

Run: `just --list`
Expected: All commands listed: setup, test, test-cov, list-gpus, estimate, estimate-matrix, build-image, push-image, bench, bench-matrix, bench-matrix-capped, build-index, validate, status, dev, build-site
