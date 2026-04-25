from __future__ import annotations
import argparse
import json
import os
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

def hashcat_versions_cmd(show_all: bool = False) -> None:
    from hashcat_bench.hashcat import fetch_releases, fetch_tags, fetch_branch_head

    head = fetch_branch_head("master")
    if head:
        print(f"master       {head['date']}   HEAD @ {head['sha']} - {head['message']}")
        print()

    if show_all:
        tags = fetch_tags()
        for tag in tags:
            print(tag)
    else:
        releases = fetch_releases()
        if not releases:
            print("No releases found.", file=sys.stderr)
            return
        print(f"{'Version':12s} {'Date':12s} {'Notes':10s}")
        print("-" * 36)
        for r in releases:
            notes = "pre-release" if r["prerelease"] else ""
            print(f"{r['version']:12s} {r['date']:12s} {notes}")
        print()
        print("Tip: pass any git ref to build-image (tag, branch, or commit SHA)")


GPU_FAMILIES: dict[str, list[dict]] = {
    "rtx-50": [
        {"name": "RTX 5090", "family": "Blackwell"},
        {"name": "RTX 5080", "family": "Blackwell"},
        {"name": "RTX 5070 Ti", "family": "Blackwell"},
        {"name": "RTX 5070", "family": "Blackwell"},
    ],
    "rtx-40": [
        {"name": "RTX 4090", "family": "Ada Lovelace"},
        {"name": "RTX 4080 SUPER", "family": "Ada Lovelace"},
        {"name": "RTX 4080", "family": "Ada Lovelace"},
        {"name": "RTX 4070 Ti SUPER", "family": "Ada Lovelace"},
        {"name": "RTX 4070 Ti", "family": "Ada Lovelace"},
        {"name": "RTX 4070 SUPER", "family": "Ada Lovelace"},
        {"name": "RTX 4070", "family": "Ada Lovelace"},
        {"name": "RTX 4060 Ti", "family": "Ada Lovelace"},
        {"name": "RTX 4060", "family": "Ada Lovelace"},
    ],
    "rtx-30": [
        {"name": "RTX 3090 Ti", "family": "Ampere"},
        {"name": "RTX 3090", "family": "Ampere"},
        {"name": "RTX 3080 Ti", "family": "Ampere"},
        {"name": "RTX 3080", "family": "Ampere"},
        {"name": "RTX 3070 Ti", "family": "Ampere"},
        {"name": "RTX 3070", "family": "Ampere"},
        {"name": "RTX 3060 Ti", "family": "Ampere"},
        {"name": "RTX 3060", "family": "Ampere"},
    ],
    "rtx-20": [
        {"name": "RTX 2080 Ti", "family": "Turing"},
        {"name": "RTX 2080 SUPER", "family": "Turing"},
        {"name": "RTX 2080", "family": "Turing"},
        {"name": "RTX 2070 SUPER", "family": "Turing"},
        {"name": "RTX 2070", "family": "Turing"},
        {"name": "RTX 2060 SUPER", "family": "Turing"},
        {"name": "RTX 2060", "family": "Turing"},
    ],
    "gtx-16": [
        {"name": "GTX 1660 Ti", "family": "Turing"},
        {"name": "GTX 1660 SUPER", "family": "Turing"},
        {"name": "GTX 1660", "family": "Turing"},
        {"name": "GTX 1650 SUPER", "family": "Turing"},
        {"name": "GTX 1650", "family": "Turing"},
    ],
    "gtx-10": [
        {"name": "GTX 1080 Ti", "family": "Pascal"},
        {"name": "GTX 1080", "family": "Pascal"},
        {"name": "GTX 1070 Ti", "family": "Pascal"},
        {"name": "GTX 1070", "family": "Pascal"},
        {"name": "GTX 1060", "family": "Pascal"},
    ],
    "datacenter": [
        {"name": "H100", "family": "Hopper"},
        {"name": "A100", "family": "Ampere"},
        {"name": "A10", "family": "Ampere"},
        {"name": "L4", "family": "Ada Lovelace"},
        {"name": "L40", "family": "Ada Lovelace"},
        {"name": "L40S", "family": "Ada Lovelace"},
        {"name": "T4", "family": "Turing"},
        {"name": "V100", "family": "Volta"},
    ],
}

import re as _re


def _name_to_slug(name: str) -> str:
    return _re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def add_gpu_cmd(data_dir: Path, names: list[str], family: str | None = None, check_vastai: bool = False) -> None:
    from hashcat_bench.models import GpuModel

    gpu_file = data_dir / "gpu-models.json"
    registry = GpuModelRegistry.load(gpu_file)

    to_add: list[dict] = []

    for name in names:
        if name in GPU_FAMILIES:
            to_add.extend(GPU_FAMILIES[name])
        else:
            to_add.append({"name": name, "family": family or "Unknown"})

    added = 0
    skipped = 0
    for entry in to_add:
        slug = _name_to_slug(entry["name"])
        if registry.has_slug(slug):
            print(f"  {entry['name']:24s} skip (already in list)")
            skipped += 1
            continue

        model = GpuModel(
            name=entry["name"],
            slug=slug,
            family=entry["family"],
            vendor="nvidia",
            vastai_name=entry["name"],
        )
        registry.add(model)
        print(f"  {entry['name']:24s} added ({entry['family']}, slug: {slug})")
        added += 1

    if added > 0:
        registry.save(gpu_file)

    print(f"\n{added} added, {skipped} skipped")

    if check_vastai and added > 0:
        print("\nChecking Vast.ai availability for new models...")
        from hashcat_bench.provider import VastProvider
        provider = VastProvider()
        for entry in to_add:
            slug = _name_to_slug(entry["name"])
            model = registry.get_by_slug(slug)
            if model is None:
                continue
            offers = provider.search_gpu(model.vastai_name)
            if offers:
                cheapest = min(offers, key=lambda o: o["dph_total"])
                print(f"  {model.name:24s} {len(offers)} offers, from ${cheapest['dph_total']:.3f}/hr")
            else:
                print(f"  {model.name:24s} not available")


def list_gpu_families_cmd() -> None:
    print("Available GPU families for bulk add:\n")
    for family_key, gpus in GPU_FAMILIES.items():
        names = ", ".join(g["name"] for g in gpus)
        print(f"  {family_key:14s} ({len(gpus)} GPUs) {names}")
    print(f"\nUsage: just add-gpu <family>     e.g. just add-gpu rtx-20")
    print(f"       just add-gpu <name>       e.g. just add-gpu 'RTX 2080 Ti'")


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
    container_registry = os.environ.get("HASHCAT_BENCH_REGISTRY", "ghcr.io/YOUR_USERNAME/hashcat-bench")
    cuda_ver = os.environ.get("HASHCAT_BENCH_CUDA", "12.9.1")
    image = f"{container_registry}:{hashcat_version}-cuda{cuda_ver}"
    provider = VastProvider()
    runner = BenchmarkRunner(provider=provider)
    print(f"Benchmarking {model.name} @ {hashcat_version} ({kernel_mode})...")
    result = runner.run(vastai_name=model.vastai_name, image=image, hashcat_version=hashcat_version, kernel_mode=kernel_mode)
    path = dm.save_result(result)
    print(f"Result saved to {path}")

def bench_matrix_cmd(data_dir: Path, hashcat_version: str, kernel_mode: str = "optimized", budget_cap: float | None = None) -> None:
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
    p_hv = sub.add_parser("hashcat-versions", help="List available hashcat versions from GitHub")
    p_hv.add_argument("--all", action="store_true", dest="show_all", help="Show all tags, not just releases")
    p_add = sub.add_parser("add-gpu", help="Add GPU model(s) to the tracking list")
    p_add.add_argument("names", nargs="+", help="GPU name(s) or family keys (rtx-20, datacenter, etc.)")
    p_add.add_argument("--family", help="GPU family (auto-detected for known families)")
    p_add.add_argument("--check", action="store_true", help="Check Vast.ai availability after adding")
    sub.add_parser("gpu-families", help="List available GPU family keys for bulk add")
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
    elif args.command == "hashcat-versions":
        hashcat_versions_cmd(args.show_all)
    elif args.command == "status":
        status_cmd(args.data_dir, args.versions)
    elif args.command == "add-gpu":
        add_gpu_cmd(args.data_dir, args.names, args.family, args.check)
    elif args.command == "gpu-families":
        list_gpu_families_cmd()
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
