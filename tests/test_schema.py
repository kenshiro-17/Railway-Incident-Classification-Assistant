from __future__ import annotations

import unittest
from datetime import UTC, datetime

from pydantic import ValidationError

from app.models.schemas import IncidentInput


class SchemaTest(unittest.TestCase):
    def test_incident_language_validation(self) -> None:
        item = IncidentInput(
            timestamp=datetime.now(UTC),
            line_or_route="Line-A",
            train_type="EMU",
            symptoms="Brake issue",
            language="en"
        )
        self.assertEqual(item.language, "en")

        with self.assertRaises(ValidationError):
            IncidentInput(
                timestamp=datetime.now(UTC),
                line_or_route="Line-A",
                train_type="EMU",
                symptoms="Brake issue",
                language="fr"
            )


if __name__ == "__main__":
    unittest.main()
