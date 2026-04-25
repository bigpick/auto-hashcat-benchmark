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
    provider = _mock_provider({"RTX 4090": [{"id": 1, "dph_total": 0.40, "reliability": 0.95}]})
    estimator = CostEstimator(provider)
    est = estimator.estimate_single("RTX 4090", estimated_minutes=15)
    assert est.gpu_name == "RTX 4090"
    assert est.price_per_hour == 0.40
    assert est.estimated_minutes == 15
    assert 0.14 < est.estimated_cost < 0.16

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
    provider = _mock_provider({"RTX 4090": [{"id": 1, "dph_total": 0.40, "reliability": 0.95}]})
    models = [GpuModel(name="RTX 4090", slug="rtx-4090", family="Ada Lovelace", vendor="nvidia", vastai_name="RTX 4090")]
    estimator = CostEstimator(provider)
    estimates = estimator.estimate_matrix(models, skip_slugs=["rtx-4090"])
    total = estimator.total_cost(estimates)
    assert total == 0.0
