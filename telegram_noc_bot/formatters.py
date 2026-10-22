from __future__ import annotations

from html import escape
from typing import Any


def _value(item: dict[str, Any], key: str, default: str = "-") -> str:
    value = item.get(key)
    return default if value is None or value == "" else str(value)


def status_text(data: dict[str, Any]) -> str:
    summary = data.get("summary") or {}
    error = data.get("error")

    sensors_total = int(summary.get("sensors_total") or 0)
    # The NOC currently exposes stale sensors rather than explicit online/
    # offline counters. A stale sensor is considered offline for this summary.
    sensors_offline = int(summary.get("sensors_offline") if summary.get("sensors_offline") is not None else summary.get("sensors_stale") or 0)
    sensors_online = int(summary.get("sensors_online") if summary.get("sensors_online") is not None else max(sensors_total - sensors_offline, 0))

    lines = [
        "<b>FIC Cerezas NOC</b>",
        "",
        f"Gateways: {summary.get('gateways_online', 0)}/{summary.get('gateways_total', 0)} online",
        f"Gateways offline: {summary.get('gateways_offline', 0)}",
        f"Sensores online: {sensors_online}/{sensors_total}",
        f"Sensores offline: {sensors_offline}",
    ]
    if error:
        lines.extend(["", f"⚠️ {escape(str(error))}"])
    return "\n".join(lines)


def gateways_text(data: dict[str, Any]) -> str:
    gateways = data.get("gateways") or []
    if not gateways:
        return "No hay gateways disponibles."
    lines = ["<b>Gateways</b>"]
    for index, gateway in enumerate(gateways):
        state = "🟢 ONLINE" if gateway.get("online") else "🔴 OFFLINE"
        location_lines = []
        latitude = gateway.get("latitude")
        longitude = gateway.get("longitude")
        if latitude is not None and longitude is not None:
            coordinates = f"{latitude}, {longitude}"
            maps_url = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
            location_lines.append(f'GPS: <a href="{escape(maps_url, quote=True)}">{escape(coordinates)}</a>')
        else:
            location_lines.append("GPS: -")

        separator = "\n\n" if index else "\n"
        lines.append(
            f"{separator}{state} <b>{escape(_value(gateway, 'display_name'))}</b>\n"
            f"ID: <code>{escape(_value(gateway, 'gateway_id'))}</code>\n"
            f"{location_lines[0]}\n"
            f"Última comunicación: {escape(_value(gateway, 'last_seen_at'))}"
        )
    return "".join(lines)


def sensors_text(data: dict[str, Any], device_id: str | None = None) -> str:
    sensors = data.get("sensors") or []
    if device_id:
        sensors = [sensor for sensor in sensors if sensor.get("device_id") == device_id]
    if not sensors:
        return "No se encontró el sensor solicitado." if device_id else "No hay sensores disponibles."

    # The complete sensor inventory can exceed Telegram's message limit.
    # Keep the detail command available, but make the default inventory a
    # compact summary grouped by TTN application (beneficiario/campo).
    if not device_id:
        groups: dict[str, dict[str, int]] = {}
        for sensor in sensors:
            group = str(sensor.get("application_id") or sensor.get("site") or "Sin beneficiario/campo")
            bucket = groups.setdefault(group, {"total": 0, "online": 0, "offline": 0})
            bucket["total"] += 1
            if sensor.get("online"):
                bucket["online"] += 1
            else:
                bucket["offline"] += 1

        lines = ["<b>Sensores por beneficiario/campo</b>", f"Total: {len(sensors)}"]
        for group in sorted(groups):
            bucket = groups[group]
            lines.extend([
                "",
                f"<b>{escape(group)}</b>",
                f"Sensores: {bucket['total']} · Online: {bucket['online']} · Offline: {bucket['offline']}",
            ])
        return "\n".join(lines)

    lines = ["<b>Sensores</b>"]
    for sensor in sensors:
        lines.append(
            f"\n<b>{escape(_value(sensor, 'device_id'))}</b>\n"
            f"Sitio: {escape(_value(sensor, 'site'))}\n"
            f"Gateway: {escape(_value(sensor, 'gateway_id'))}\n"
            f"Última comunicación: {escape(_value(sensor, 'last_seen_at'))}\n"
            f"Batería: {escape(_value(sensor, 'battery_percent'))}% · RSSI: {escape(_value(sensor, 'rssi'))} dBm · SNR: {escape(_value(sensor, 'snr'))} dB"
        )
    return "".join(lines)


def alerts_text(data: dict[str, Any]) -> str:
    alerts = []
    for gateway in data.get("gateways") or []:
        if not gateway.get("online"):
            alerts.append(f"🔴 Gateway offline: {gateway.get('gateway_id', '-')}")
    for sensor in data.get("sensors") or []:
        if sensor.get("battery_percent") is not None and sensor["battery_percent"] < 20:
            alerts.append(f"🪫 Batería baja: {sensor.get('device_id', '-')} ({sensor['battery_percent']}%)")
    return "<b>Alertas</b>\n" + "\n".join(escape(item) for item in alerts) if alerts else "<b>Alertas</b>\n✅ Sin alertas activas."
