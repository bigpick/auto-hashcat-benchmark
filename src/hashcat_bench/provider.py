from __future__ import annotations

import os
from typing import Any


class VastProvider:
    def __init__(self, sdk: Any = None, api_key: str | None = None):
        if sdk is not None:
            self._sdk = sdk
        else:
            from vastai import VastAI
            key = api_key or os.environ.get("VAST_API_KEY")
            if not key:
                raise RuntimeError(
                    "VAST_API_KEY not set. Export it as an environment variable "
                    "or add it to .env (see .env.example)."
                )
            self._sdk = VastAI(api_key=key)

    def __repr__(self) -> str:
        return "VastProvider(...)"

    def search_gpu(self, vastai_name: str) -> list[dict]:
        search_name = vastai_name.replace(" ", "_")
        offers = self._sdk.search_offers(
            query=f"gpu_name={search_name} num_gpus=1 rentable=true",
            order="dph_total",
            limit="20",
        )
        if offers is None:
            return []
        return offers

    def cheapest_offer(self, vastai_name: str, min_reliability: float = 0.8) -> dict | None:
        offers = self.search_gpu(vastai_name)
        viable = [o for o in offers if o.get("reliability", 0) >= min_reliability]
        if not viable:
            return None
        return min(viable, key=lambda o: o["dph_total"])

    def create_instance(self, offer_id: int, image: str, env: dict[str, str] | None = None) -> int:
        env_str = " ".join(f"-e {k}={v}" for k, v in (env or {}).items())
        result = self._sdk.create_instance(
            id=offer_id,
            image=image,
            disk=20,
            env=env_str,
        )
        return result["new_contract"]

    def instance_status(self, instance_id: int) -> dict:
        return self._sdk.show_instance(id=instance_id)

    def destroy_instance(self, instance_id: int) -> None:
        self._sdk.destroy_instance(id=instance_id)
