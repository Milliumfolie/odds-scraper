"""Template parser for adding new bookmakers.

Minimal parser signature and example to be used by contributors and tests.
"""

from __future__ import annotations

import datetime


def parse_template(url: str | None = None, data: str | None = None, headless: bool = False) -> dict:
    """Return a dict with keys being "Team A - Team B".

    For development return a deterministic example when `data` or `url` is None so tests don't
    depend on external sites.
    """
    # Example static return used for development/tests
    return {
        "Sample A - Sample B": {
            "odds": {"template": [2.0, 3.5, 3.0]},
            "id": {"template": "1234"},
            "date": "2025-12-31T15:00:00",
            "competition": "Example League"
        }
    }


if __name__ == "__main__":
    # Quick manual test
    print(parse_template())