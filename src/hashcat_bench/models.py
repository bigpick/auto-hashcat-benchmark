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
class HostInfo:
    gpu_vram_mib: int = 0
    cpu_model: str = ""
    cpu_cores: int = 0
    ram_total_mb: int = 0
    pcie_gen: str = ""
    pcie_width: str = ""


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
    host: HostInfo = field(default_factory=HostInfo)

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
        host_data = d.get("host", {})
        host = HostInfo(**host_data) if host_data else HostInfo()
        return cls(
            hashcat_version=d["hashcat_version"],
            gpu_model=d["gpu_model"],
            container_image=d["container_image"],
            driver_version=d["driver_version"],
            cuda_version=d["cuda_version"],
            kernel_mode=d["kernel_mode"],
            benchmark_date=d["benchmark_date"],
            benchmarks=benchmarks,
            host=host,
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

    def has_slug(self, slug: str) -> bool:
        return self.get_by_slug(slug) is not None

    def add(self, model: GpuModel) -> bool:
        if self.has_slug(model.slug):
            return False
        self.models.append(model)
        return True

    def save(self, path: Path) -> None:
        data = {"models": [asdict(m) for m in self.models]}
        path.write_text(json.dumps(data, indent=2) + "\n")
