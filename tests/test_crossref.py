import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

import requests

from core.config import load_settings
from ingestion.crossref import fetch_source_records, parse_crossref_payload


class CrossrefTests(unittest.TestCase):
    def test_parse_crossref_payload_cleans_markup_and_skips_invalid_records(self):
        item = {
            "DOI": "10.1234/example",
            "title": ["  A   title  "],
            "abstract": "<jats:p>First <i>important</i> result &amp; more.</jats:p>",
            "author": [{"given": "Ada", "family": "Lovelace"}],
            "subject": ["Computing"],
            "published": {"date-parts": [[2026, 5]]},
            "link": [{"content-type": "application/pdf", "URL": "https://example.org/paper.pdf"}],
        }
        records = parse_crossref_payload({"message": {"items": [item, {"DOI": "bad"}]}})

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].summary, "First important result & more.")
        self.assertEqual(records[0].published, "2026-05-01")
        self.assertEqual(records[0].authors, ["Ada Lovelace"])
        self.assertEqual(records[0].pdf_url, "https://example.org/paper.pdf")

    def test_fetch_preserves_live_response_and_falls_back_to_snapshot(self):
        settings = load_settings()
        fixture = Path(__file__).resolve().parents[1] / "data/raw/crossref_response.json"
        original_bytes = fixture.read_bytes()
        payload = json.loads(original_bytes)
        response = Mock()
        response.content = original_bytes
        response.json.return_value = payload
        response.raise_for_status.return_value = None

        with patch("requests.Session.get", return_value=response) as get, \
             patch("ingestion.crossref.ensure_parent"), \
             patch("ingestion.crossref.Path.write_bytes") as write_raw, \
             patch("ingestion.crossref.write_json") as write_records:
            records = fetch_source_records(settings)
        self.assertEqual(len(records), 24)
        write_raw.assert_called_once_with(original_bytes)
        self.assertEqual(len(write_records.call_args.args[1]), 24)
        self.assertEqual(get.call_args.kwargs["params"]["rows"], settings.max_results)

        with patch("requests.Session.get", side_effect=requests.ConnectionError("offline")), \
             patch("ingestion.crossref.read_json", return_value=payload), \
             patch("ingestion.crossref.write_json") as write_records, \
             patch("ingestion.crossref.Path.write_bytes") as write_raw:
            offline_records = fetch_source_records(settings)
        self.assertEqual(offline_records, records)
        write_raw.assert_not_called()
        self.assertEqual(len(write_records.call_args.args[1]), 24)
