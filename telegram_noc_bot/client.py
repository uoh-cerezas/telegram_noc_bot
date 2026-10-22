from __future__ import annotations

from datetime import datetime, timezone
import math
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
            {"device_id": "sensor-rengo-01", "site": "rengo", "gateway_id": "gw-rengo-01", "latitude": -34.406, "longitude": -70.858, "last_seen_at": now, "online": True, "battery_percent": 87, "rssi": -81, "snr": 8.4},
            {"device_id": "sensor-sanfernando-01", "site": "sanfernando", "gateway_id": "gw-sanfernando-01", "latitude": -34.584, "longitude": -70.991, "last_seen_at": now, "online": False, "battery_percent": 42, "rssi": -116, "snr": -12.2},
        ]
        return _keep_located_sensors({"generated_at": now, "mode": "mock", "error": None, "summary": {"gateways_total": 2, "gateways_online": 1, "gateways_offline": 1, "sensors_total": 2, "sensors_stale": 0}, "gateways": gateways, "sensors": sensors})


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
            return _keep_located_sensors(response.json())
        except (requests.RequestException, ValueError) as error:
            raise NocClientError(str(error)) from error


def _keep_located_sensors(data: dict[str, Any]) -> dict[str, Any]:
    """Keep only sensors with valid GPS coordinates and recalculate totals."""
    sensors = [sensor for sensor in data.get("sensors") or [] if _has_gps(sensor)]
    result = dict(data)
    result["sensors"] = sensors
    summary = dict(result.get("summary") or {})
    online = sum(1 for sensor in sensors if sensor.get("online"))
    offline = len(sensors) - online
    summary.update(
        sensors_total=len(sensors),
        sensors_online=online,
        sensors_offline=offline,
        sensors_stale=offline,
    )
    result["summary"] = summary
    return result


def _has_gps(sensor: dict[str, Any]) -> bool:
    try:
        return math.isfinite(float(sensor.get("latitude"))) and math.isfinite(float(sensor.get("longitude")))
    except (TypeError, ValueError):
        return False
