from __future__ import annotations

import shlex
from typing import Any

from .client import NocClientError
from .formatters import alerts_text, gateways_text, sensors_text, status_text


HELP_TEXT = """<b>Comandos NOC</b>

/status — resumen general
/gateways — estado de gateways
/sensors — estado de sensores
/sensor &lt;device_id&gt; — detalle de un sensor
/gateway &lt;gateway_id&gt; — detalle de un gateway
/alerts — alertas activas
/help — muestra esta ayuda"""


def execute(command: str, client: Any) -> str:
    try:
        parts = shlex.split(command.strip())
    except ValueError:
        return "Comando no válido. Usa /help."
    if not parts:
        return HELP_TEXT
    name = parts[0].split("@", 1)[0].lower()
    if name in {"/start", "/help"}:
        return HELP_TEXT
    if name not in {"/status", "/gateways", "/sensors", "/sensor", "/gateway", "/alerts"}:
        return "Comando no reconocido. Usa /help."
    if name == "/sensor" and len(parts) < 2:
        return "Uso: /sensor <device_id>"
    if name == "/gateway" and len(parts) < 2:
        return "Uso: /gateway <gateway_id>"
    try:
        data = client.status()
    except NocClientError as error:
        return f"⚠️ No se pudo consultar el NOC: {error}"
    if name == "/status":
        return status_text(data)
    if name == "/gateways":
        return gateways_text(data)
    if name == "/sensors":
        return sensors_text(data)
    if name == "/sensor":
        return sensors_text(data, parts[1])
    if name == "/gateway":
        gateway_id = parts[1]
        gateways = [gateway for gateway in data.get("gateways", []) if gateway.get("gateway_id") == gateway_id]
        return gateways_text({"gateways": gateways})
    if name == "/alerts":
        return alerts_text(data)
    return "Comando no reconocido. Usa /help."
