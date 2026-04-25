#!/usr/bin/env bash
set -euo pipefail

KERNEL_MODE="${KERNEL_MODE:-optimized}"
BENCHMARK_ALL="${BENCHMARK_ALL:-false}"
HASHCAT_VERSION="${HASHCAT_VERSION:-unknown}"
CONTAINER_IMAGE="${CONTAINER_IMAGE:-unknown}"
CUDA_VERSION="${CUDA_VERSION:-12.9.1}"

# Find the hashcat binary (system-installed or local in /root/hashcat)
if command -v hashcat &>/dev/null; then
    HASHCAT_BIN="hashcat"
elif [ -x /root/hashcat/hashcat ]; then
    HASHCAT_BIN="/root/hashcat/hashcat"
else
    echo "ERROR: hashcat binary not found" >&2
    exit 1
fi

# GPU info
gpu_info=$(nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader)
gpu_name=$(echo "$gpu_info" | cut -d',' -f1 | xargs)
driver_version=$(echo "$gpu_info" | cut -d',' -f2 | xargs)
gpu_vram_mib=$(echo "$gpu_info" | cut -d',' -f3 | sed 's/[^0-9]//g')

# Host hardware info
cpu_model=$(grep -m1 'model name' /proc/cpuinfo 2>/dev/null | cut -d: -f2 | xargs || echo "unknown")
cpu_cores=$(nproc 2>/dev/null || echo "0")
ram_total_mb=$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print int($2/1024)}' || echo "0")
pcie_info=$(nvidia-smi --query-gpu=pcie.link.gen.current,pcie.link.width.current --format=csv,noheader 2>/dev/null || echo "unknown,unknown")
pcie_gen=$(echo "$pcie_info" | cut -d',' -f1 | xargs)
pcie_width=$(echo "$pcie_info" | cut -d',' -f2 | xargs)

# Run benchmark
hashcat_flags="--machine-readable"
if [ "$BENCHMARK_ALL" = "true" ]; then
    hashcat_flags="$hashcat_flags --benchmark-all"
else
    hashcat_flags="$hashcat_flags -b"
fi
if [ "$KERNEL_MODE" = "optimized" ]; then
    hashcat_flags="$hashcat_flags -O"
fi

echo "Running: $HASHCAT_BIN $hashcat_flags" >&2
benchmark_output=$($HASHCAT_BIN $hashcat_flags 2>/tmp/hashcat_stderr.log)
hashcat_exit=$?
if [ $hashcat_exit -ne 0 ]; then
    echo "ERROR: hashcat exited with code $hashcat_exit" >&2
    cat /tmp/hashcat_stderr.log >&2
    exit $hashcat_exit
fi

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
    --arg gpu_vram_mib "$gpu_vram_mib" \
    --arg cpu_model "$cpu_model" \
    --arg cpu_cores "$cpu_cores" \
    --arg ram_total_mb "$ram_total_mb" \
    --arg pcie_gen "$pcie_gen" \
    --arg pcie_width "$pcie_width" \
    '{
        hashcat_version: $hv,
        gpu_model: $gm,
        container_image: $ci,
        driver_version: $dv,
        cuda_version: $cv,
        kernel_mode: $km,
        benchmark_date: $bd,
        host: {
            gpu_vram_mib: ($gpu_vram_mib | tonumber),
            cpu_model: $cpu_model,
            cpu_cores: ($cpu_cores | tonumber),
            ram_total_mb: ($ram_total_mb | tonumber),
            pcie_gen: $pcie_gen,
            pcie_width: $pcie_width
        },
        benchmarks: $bm
    }' | tee /tmp/result.json
