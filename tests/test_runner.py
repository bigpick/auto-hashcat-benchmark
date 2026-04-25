import json
from unittest.mock import MagicMock, patch
from hashcat_bench.runner import BenchmarkRunner


def _make_provider():
    provider = MagicMock()
    provider.ensure_ssh_key.return_value = "ssh-ed25519 AAAA..."
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
        "hashcat_version": "v6.2.6", "gpu_model": "RTX 4090", "container_image": "img",
        "driver_version": "535", "cuda_version": "12.2", "kernel_mode": "optimized",
        "benchmark_date": "2026-01-01T00:00:00Z", "benchmarks": [],
    }
    with patch.object(runner, "_collect_results", return_value=json.dumps(sample_result)):
        with patch("hashcat_bench.runner.time") as mock_time:
            mock_time.sleep = MagicMock()
            mock_time.time = MagicMock(side_effect=range(0, 100, 5))
            result = runner.run(
                vastai_name="RTX 4090",
                image="ghcr.io/user/hashcat-bench:v6.2.6-cuda12.2",
                hashcat_version="v6.2.6",
                kernel_mode="optimized",
            )
    provider.ensure_ssh_key.assert_called_once()
    provider.cheapest_offer.assert_called_once_with("RTX 4090", min_cuda=12.9)
    provider.create_instance.assert_called_once()
    provider.destroy_instance.assert_called_once_with(789)
    assert result.hashcat_version == "v6.2.6"


def test_run_no_offers_raises():
    provider = MagicMock()
    provider.ensure_ssh_key.return_value = "ssh-ed25519 AAAA..."
    provider.cheapest_offer.return_value = None
    runner = BenchmarkRunner(provider=provider)
    try:
        runner.run(vastai_name="RTX 9999", image="img", hashcat_version="v6.2.6", kernel_mode="optimized")
        assert False, "Should have raised"
    except RuntimeError as e:
        assert "No available offers" in str(e)


def test_run_destroys_on_failure():
    provider = MagicMock()
    provider.ensure_ssh_key.return_value = "ssh-ed25519 AAAA..."
    provider.cheapest_offer.return_value = {"id": 100, "dph_total": 0.35}
    provider.create_instance.return_value = 789
    provider.instance_status.side_effect = Exception("API error")
    runner = BenchmarkRunner(provider=provider)
    try:
        with patch("hashcat_bench.runner.time") as mock_time:
            mock_time.sleep = MagicMock()
            mock_time.time = MagicMock(side_effect=range(0, 100, 5))
            runner.run(vastai_name="RTX 4090", image="img", hashcat_version="v6.2.6", kernel_mode="optimized")
        assert False, "Should have raised"
    except Exception:
        pass
    provider.destroy_instance.assert_called_once_with(789)
