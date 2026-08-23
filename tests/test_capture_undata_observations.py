from __future__ import annotations

from io import BytesIO
from pathlib import Path
import sys
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "adapters"))

import capture_undata_observations as capture


class UNdataObservationCaptureTests(unittest.TestCase):
    def test_safe_name_is_stable(self) -> None:
        self.assertEqual(capture.safe_name("GDP per capita (US$)"), "gdp-per-capita-us")

    def test_zip_summary_counts_csv_data_rows(self) -> None:
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("observations.csv", "country,year,value\nAAA,2025,1\nBBB,2025,2\n")
        summary = capture.zip_summary(buffer.getvalue())
        self.assertEqual(summary["members"][0]["data_row_count"], 2)


if __name__ == "__main__":
    unittest.main()
