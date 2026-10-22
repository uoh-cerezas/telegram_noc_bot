import os
import unittest

os.environ["TELEGRAM_MODE"] = "mock"

from telegram_noc_bot.client import MockNocClient
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


if __name__ == "__main__":
    unittest.main()
