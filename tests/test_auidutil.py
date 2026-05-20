"""
Unit tests for AuidGenerator.
"""

import unittest

from lockss.pybasic.auidutil import AuidGenerator


class TestAuidGeneration(unittest.TestCase):
    """Test AUID generation."""

    def test_generate_auid_real_world_example(self):
        """Test generating AUID with real-world plugin."""
        plugin_id = "org.lockss.plugin.clockss.aps.ClockssAPSSourcePlugin"
        params = {
            "base_url": "http://clockss-ingest.clockss.org/sourcefiles/aps-released/",
            "year": "2020",
            "utf8param": "éöf oo"
        }

        auid = AuidGenerator.generate_auid(plugin_id, params)
        # Note: Periods are encoded as %2E per Java PropKeyEncoder
        expected = "org|lockss|plugin|clockss|aps|ClockssAPSSourcePlugin&base_url~http%3A%2F%2Fclockss-ingest%2Eclockss%2Eorg%2Fsourcefiles%2Faps-released%2F&utf8param~%C3%A9%C3%B6f+oo&year~2020"
        self.assertEqual(auid, expected)

        """Test decoding AUID to parameters."""
        result = AuidGenerator.decode_auid(auid)
        self.assertEqual(result, params)


if __name__ == "__main__":
    unittest.main()
