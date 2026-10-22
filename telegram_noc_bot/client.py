from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

try:
    import requests
except ImportError:  # Mock mode can be tested without optional HTTP dependencies.
    requests = None


class NocClientError(RuntimeError):
    pass


class MockNocClient:
    def status(self) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        gateways = [
            {"gateway_id": "gw-rengo-01", "display_name": "Gateway Rengo 01", "site": "rengo", "online": True, "last_seen_at": now},
            {"gateway_id": "gw-sanfernando-01", "display_name": "Gateway San Fernando 01", "site": "sanfernando", "online": False, "last_seen_at": now},
        ]
        sensors = [
            {"device_id": "sensor-rengo-01", "site": "rengo", "gateway_id": "gw-rengo-01", "last_seen_at": now, "online": True, "battery_percent": 87, "rssi": -81, "snr": 8.4},
            {"device_id": "sensor-sanfernando-01", "site": "sanfernando", "gateway_id": "gw-sanfernando-01", "last_seen_at": now, "online": False, "battery_percent": 42, "rssi": -116, "snr": -12.2},
        ]
        return {"generated_at": now, "mode": "mock", "error": None, "summary": {"gateways_total": 2, "gateways_online": 1, "gateways_offline": 1, "sensors_total": 2, "sensors_stale": 0}, "gateways": gateways, "sensors": sensors}


class HttpNocClient:
    def __init__(self, base_url: str, timeout: float = 10) -> None:
        self.base_url = base_url
        self.timeout = timeout

    def status(self) -> dict[str, Any]:
        if requests is None:
            raise NocClientError("requests is not installed")
        try:
            response = requests.get(f"{self.base_url}/api/status", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as error:
            raise NocClientError(str(error)) from error
