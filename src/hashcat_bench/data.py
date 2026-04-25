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
