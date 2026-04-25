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

    def estimate_single(self, vastai_name: str, estimated_minutes: float = DEFAULT_RUNTIME_MINUTES) -> CostEstimate:
        offer = self._provider.cheapest_offer(vastai_name)
        if offer is None:
            return CostEstimate(gpu_name=vastai_name, available=False)
        price_per_hour = offer["dph_total"]
        hours = (estimated_minutes / 60.0) * SAFETY_MULTIPLIER
        cost = price_per_hour * hours
        return CostEstimate(
            gpu_name=vastai_name, available=True, price_per_hour=price_per_hour,
            estimated_minutes=estimated_minutes, estimated_cost=round(cost, 4),
        )

    def estimate_matrix(self, models: list[GpuModel], skip_slugs: list[str] | None = None) -> list[CostEstimate]:
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
