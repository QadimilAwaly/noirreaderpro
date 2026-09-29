#!/usr/bin/env bash
set -euo pipefail

# Noir Reader Pro — Autoresearch Canonical Benchmark Entrypoint
# Runs deterministic end-to-end simulated client reading workload
# Measuring overall latency, endpoint latencies, CPU time, and transferred payload.

cd "$(dirname "$0")"

# Execute deterministic benchmark workload
python3 benchmarks/run_benchmark.py
