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

def list_gpus_cmd(data_dir: Path, filter_str: str | None = None) -> None:
    from hashcat_bench.provider import VastProvider
    gpu_file = data_dir / "gpu-models.json"
    registry = GpuModelRegistry.load(gpu_file)
    gpu_names = [m.vastai_name for m in registry.models]
    if filter_str:
        gpu_names = [g for g in gpu_names if filter_str.lower() in g.lower()]
    provider = VastProvider()
    print(f"{'GPU':30s}  {'Available':>9s}  {'$/hr':>8s}")
    print("-" * 53)
    for name in gpu_names:
        offers = provider.search_gpu(name)
        if offers:
            cheapest = min(offers, key=lambda o: o["dph_total"])
            price = f"${cheapest['dph_total']:.3f}"
            print(f"{name:30s}  {len(offers):>9d}  {price:>8s}")
        else:
            print(f"{name:30s}  {'none':>9s}  {'n/a':>8s}")

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


from hashcat_bench.gpu_catalog import GPU_FAMILIES

import re as _re


def _name_to_slug(name: str) -> str:
    return _re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def add_gpu_cmd(data_dir: Path, names: list[str], family: str | None = None, check_vastai: bool = False) -> None:
    from hashcat_bench.models import GpuModel

    gpu_file = data_dir / "gpu-models.json"
    registry = GpuModelRegistry.load(gpu_file)

    to_add: list[dict] = []

    for name in names:
        if name == "all":
            for fam in GPU_FAMILIES.values():
                to_add.extend(fam)
        elif name in GPU_FAMILIES:
            to_add.extend(GPU_FAMILIES[name])
        elif name.lower().replace(" ", "-") in GPU_FAMILIES:
            to_add.extend(GPU_FAMILIES[name.lower().replace(" ", "-")])
        else:
            if not family:
                print(f"  WARNING: '{name}' is not a known family key. Use --family to specify the architecture.")
                print(f"           Known families: {', '.join(GPU_FAMILIES.keys())}")
                print(f"           Adding anyway with family 'Unknown'.\n")
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


def bench_cmd(data_dir: Path, gpu_slug: str, hashcat_version: str, kernel_mode: str = "optimized", benchmark_all: bool = False) -> None:
    from hashcat_bench.provider import VastProvider
    from hashcat_bench.runner import BenchmarkRunner
    gpu_file = data_dir / "gpu-models.json"
    registry = GpuModelRegistry.load(gpu_file)
    model = registry.get_by_slug(gpu_slug)
    if model is None:
        print(f"Error: unknown GPU slug '{gpu_slug}'", file=sys.stderr)
        sys.exit(1)
    dm = DataManager(data_dir)
    scope = "all" if benchmark_all else "standard"
    file_slug = gpu_slug
    if kernel_mode == "default":
        file_slug += "-default"
    if benchmark_all:
        file_slug += "-all"
    if dm.result_exists(hashcat_version, file_slug, kernel_mode):
        print(f"Already benchmarked: {model.name} @ {hashcat_version} ({kernel_mode}, {scope})")
        return
    container_registry = os.environ.get("HASHCAT_BENCH_REGISTRY", "ghcr.io/YOUR_USERNAME/hashcat-bench")
    cuda_ver = os.environ.get("HASHCAT_BENCH_CUDA", "12.9.1")
    image = f"{container_registry}:{hashcat_version}-cuda{cuda_ver}"
    provider = VastProvider()
    runner = BenchmarkRunner(provider=provider)
    scope_label = "benchmark-all" if benchmark_all else "benchmark"
    print(f"Running {scope_label}: {model.name} @ {hashcat_version} ({kernel_mode})...")
    result = runner.run(
        vastai_name=model.vastai_name, image=image,
        hashcat_version=hashcat_version, kernel_mode=kernel_mode,
        benchmark_all=benchmark_all,
    )
    path = dm.save_result(result)
    print(f"Result saved to {path}")

def bench_matrix_cmd(data_dir: Path, hashcat_version: str, kernel_mode: str = "optimized", benchmark_all: bool = False, budget_cap: float | None = None) -> None:
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

    succeeded = []
    failed = []
    for slug in missing_slugs:
        print(f"\n--- {slug} ---")
        try:
            bench_cmd(data_dir, slug, hashcat_version, kernel_mode, benchmark_all)
            succeeded.append(slug)
        except Exception as e:
            print(f"  FAILED: {e}", file=sys.stderr)
            failed.append((slug, str(e)))

    print(f"\n{'=' * 40}")
    print(f"Matrix complete: {len(succeeded)} succeeded, {len(failed)} failed")
    if failed:
        print("\nFailed GPUs:")
        for slug, err in failed:
            print(f"  {slug}: {err}")


def cleanup_cmd() -> None:
    from hashcat_bench.provider import VastProvider
    provider = VastProvider()
    instances = provider.list_instances()
    if not instances:
        print("No active instances found.")
        return
    print(f"Found {len(instances)} active instance(s):\n")
    for inst in instances:
        inst_id = inst.get("id", "?")
        status = inst.get("actual_status", "unknown")
        gpu = inst.get("gpu_name", "unknown")
        started = inst.get("start_date", "?")
        print(f"  ID {inst_id:>8}  {gpu:20s}  status={status}  started={started}")

    answer = input(f"\nDestroy all {len(instances)} instance(s)? [y/N] ")
    if answer.strip().lower() == "y":
        for inst in instances:
            inst_id = inst["id"]
            print(f"  Destroying {inst_id}...")
            provider.destroy_instance(inst_id)
        print("Done.")
    else:
        print("Aborted.")

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
    p_bench.add_argument("--benchmark-all", action="store_true", help="Use --benchmark-all (all hash modes including slow ones)")
    p_bm = sub.add_parser("bench-matrix", help="Run benchmarks for all GPUs")
    p_bm.add_argument("--hashcat", required=True, help="Hashcat version")
    p_bm.add_argument("--kernel-mode", default="optimized", choices=["optimized", "default"])
    p_bm.add_argument("--benchmark-all", action="store_true", help="Use --benchmark-all (all hash modes including slow ones)")
    p_bm.add_argument("--budget-cap", type=float, help="Max $ to spend")
    sub.add_parser("cleanup", help="List and destroy any active Vast.ai instances")
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
        list_gpus_cmd(args.data_dir, args.filter_str)
    elif args.command == "estimate":
        estimate_cmd(args.data_dir, args.gpu, args.hashcat)
    elif args.command == "estimate-matrix":
        estimate_matrix_cmd(args.data_dir, args.hashcat)
    elif args.command == "bench":
        bench_cmd(args.data_dir, args.gpu, args.hashcat, args.kernel_mode, args.benchmark_all)
    elif args.command == "bench-matrix":
        bench_matrix_cmd(args.data_dir, args.hashcat, args.kernel_mode, args.benchmark_all, args.budget_cap)
    elif args.command == "cleanup":
        cleanup_cmd()
