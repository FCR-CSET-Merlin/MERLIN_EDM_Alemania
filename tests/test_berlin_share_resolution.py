"""Contract tests for the annual Berlin sector-share policy."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "prototipo_3/preprocessing/berlin_training_contract_2023.py"
SHARES = REPO / "corfo-report/validation/berlin/berlin_sector_shares_2023.csv"


def load_contract_module():
    spec = importlib.util.spec_from_file_location("berlin_training_contract", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BerlinShareResolutionTests(unittest.TestCase):
    def test_pilot_uses_one_annual_share_row(self):
        module = load_contract_module()
        shares = module.read_shares(SHARES)
        self.assertEqual(shares["year"], 2023)
        self.assertEqual(shares["temporal_resolution"], "annual_broadcast")
        self.assertAlmostEqual(
            sum(shares[column] for column in module.SHARE_COLUMNS),
            1.0,
            places=9,
        )


if __name__ == "__main__":
    unittest.main()
