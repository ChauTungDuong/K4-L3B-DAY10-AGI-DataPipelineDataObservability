from dataclasses import replace
from datetime import datetime, timezone
import unittest

from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import PaperRecord


class CleaningTests(unittest.TestCase):
    def test_normalizes_dates_text_and_removes_duplicate_dois(self):
        record = PaperRecord(
            paper_id=" 10.1234/Example ",
            title="  A   useful title ",
            summary="<jats:p>Some  useful   findings &amp; details.</jats:p>",
            authors=[" Ada   Lovelace ", " Grace Hopper "],
            categories=[" Computer   Science "],
            primary_category="",
            published="2026-09-01",
            updated="bad date",
            abs_url="https://doi.org/10.1234/Example",
            pdf_url="",
            comment="",
        )
        duplicate = replace(record, paper_id="10.1234/example", title="Duplicate")
        invalid = replace(record, paper_id="10.1234/invalid", published="not a date")
        df = build_clean_dataframe(
            [record, duplicate, invalid], datetime(2026, 9, 26, tzinfo=timezone.utc)
        )

        self.assertEqual(len(df), 1)
        row = df.iloc[0]
        self.assertEqual(row["title"], "A useful title")
        self.assertEqual(row["summary"], "Some useful findings & details.")
        self.assertEqual(row["authors_joined"], "Ada Lovelace, Grace Hopper")
        self.assertEqual(row["categories_joined"], "Computer Science")
        self.assertEqual(row["published"], "2026-09-01")
        self.assertEqual(row["updated"], "2026-09-01")
        self.assertEqual(row["age_days"], 25)
        self.assertEqual(row["summary_chars"], len(row["summary"]))
        self.assertEqual(
            row["text_for_embedding"],
            "Title: A useful title\n"
            "Authors: Ada Lovelace, Grace Hopper\n"
            "Published: 2026-09-01\n"
            "Categories: Computer Science\n"
            "Summary: Some useful findings & details.",
        )
