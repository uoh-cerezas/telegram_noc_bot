import os
import unittest

os.environ["TELEGRAM_MODE"] = "mock"

from telegram_noc_bot.client import MockNocClient, _keep_located_sensors
from telegram_noc_bot.commands import execute


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.client = MockNocClient()

    def test_status(self):
        text = execute("/status", self.client)
        self.assertIn("FIC Cerezas NOC", text)
        self.assertIn("Gateways", text)

    def test_sensor_lookup(self):
        text = execute("/sensor sensor-rengo-01", self.client)
        self.assertIn("sensor-rengo-01", text)
        self.assertIn("Batería: 87%", text)

    def test_unknown_command(self):
        self.assertIn("/help", execute("/unknown", self.client))

    def test_sensors_without_gps_are_excluded(self):
        data = _keep_located_sensors({
            "summary": {},
            "sensors": [
                {"device_id": "located", "latitude": -34.4, "longitude": -70.8, "online": True},
                {"device_id": "no-location", "latitude": None, "longitude": None, "online": True},
            ],
        })
        self.assertEqual([sensor["device_id"] for sensor in data["sensors"]], ["located"])
        self.assertEqual(data["summary"]["sensors_total"], 1)


if __name__ == "__main__":
    unittest.main()
