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
        {"id": 456, "gpu_name": "RTX_4090", "dph_total": 0.50, "num_gpus": 1, "reliability": 0.95, "cuda_max_good": 12.2, "cpu_ram": 32768, "cpu_cores_effective": 8},
        {"id": 123, "gpu_name": "RTX_4090", "dph_total": 0.30, "num_gpus": 1, "reliability": 0.95, "cuda_max_good": 12.2, "cpu_ram": 32768, "cpu_cores_effective": 8},
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
