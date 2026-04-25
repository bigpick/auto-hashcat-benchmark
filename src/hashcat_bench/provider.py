from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

_API_KEY_RE = re.compile(r"api_key=[a-f0-9]+", re.IGNORECASE)


def _sanitize_error(exc: Exception) -> str:
    return _API_KEY_RE.sub("api_key=REDACTED", str(exc))


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
        try:
            offers = self._sdk.search_offers(
                query=f"gpu_name={search_name} num_gpus=1 rentable=true",
                order="dph_total",
                limit="20",
            )
        except Exception as e:
            raise RuntimeError(_sanitize_error(e)) from None
        if offers is None:
            return []
        return offers

    def cheapest_offer(
        self,
        vastai_name: str,
        min_reliability: float = 0.8,
        min_ram_mb: int = 16384,
        min_cpu_cores: int = 4,
    ) -> dict | None:
        offers = self.search_gpu(vastai_name)
        viable = [
            o for o in offers
            if o.get("reliability", 0) >= min_reliability
            and o.get("cpu_ram", 0) >= min_ram_mb
            and o.get("cpu_cores_effective", 0) >= min_cpu_cores
        ]
        if not viable:
            return None
        return min(viable, key=lambda o: o["dph_total"])

    def ensure_ssh_key(self, pub_key_path: Path | None = None) -> str:
        if pub_key_path is None:
            pub_key_path = Path(os.environ.get(
                "HASHCAT_BENCH_SSH_KEY",
                str(Path.home() / ".ssh" / "id_ed25519.pub"),
            ))
        if not pub_key_path.exists():
            alt = pub_key_path.parent / "id_rsa.pub"
            if alt.exists():
                pub_key_path = alt
            else:
                raise RuntimeError(
                    f"No SSH public key found at {pub_key_path} or {alt}. "
                    "Generate one with: ssh-keygen -t ed25519"
                )

        pub_key = pub_key_path.read_text().strip()
        key_fingerprint = pub_key.split()[1][:20] if len(pub_key.split()) >= 2 else pub_key[:20]

        try:
            existing = self._sdk.show_ssh_keys()
            if existing:
                keys_list = existing if isinstance(existing, list) else existing.get("ssh_keys", [])
                for k in keys_list:
                    stored = k.get("ssh_key", "") if isinstance(k, dict) else str(k)
                    if key_fingerprint in stored:
                        return pub_key
        except Exception:
            pass

        try:
            self._sdk.create_ssh_key(ssh_key=pub_key)
        except Exception:
            pass

        return pub_key

    def create_instance(self, offer_id: int, image: str, env: dict[str, str] | None = None) -> int:
        try:
            result = self._sdk.create_instance(
                id=offer_id,
                image=image,
                disk=20,
                env=env or {},
            )
        except Exception as e:
            raise RuntimeError(_sanitize_error(e)) from None
        return result["new_contract"]

    def instance_status(self, instance_id: int) -> dict:
        try:
            return self._sdk.show_instance(id=instance_id)
        except Exception as e:
            raise RuntimeError(_sanitize_error(e)) from None

    def destroy_instance(self, instance_id: int) -> None:
        try:
            self._sdk.destroy_instance(id=instance_id)
        except Exception as e:
            raise RuntimeError(_sanitize_error(e)) from None

    def list_instances(self) -> list[dict]:
        result = self._sdk.show_instances()
        if result is None:
            return []
        return result
