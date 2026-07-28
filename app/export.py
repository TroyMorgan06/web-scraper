"""CSV export of price history."""

import csv
from pathlib import Path

from app.db import get_history


def export_history_csv(output_path, product_id=None) -> Path:
    """Write price history to a CSV file and return the Path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    rows = get_history(product_id)
    fieldnames = [
        "id",
        "product_id",
        "url",
        "title",
        "price",
        "availability",
        "scraped_at",
    ]

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    return path