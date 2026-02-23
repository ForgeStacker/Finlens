"""CSV export utilities for workbook outputs."""
from __future__ import annotations

import os

import pandas as pd

from aws_utils import sanitize_filename


def export_workbook_sheets_to_csv(workbook, csv_dir: str) -> None:
    os.makedirs(csv_dir, exist_ok=True)
    for worksheet in workbook.worksheets:
        rows = []
        max_columns = 0
        for row in worksheet.iter_rows(values_only=True):
            values = ["" if cell is None else cell for cell in row]
            rows.append(values)
            if len(values) > max_columns:
                max_columns = len(values)
        while rows and all(cell == "" for cell in rows[-1]):
            rows.pop()
        if not rows or max_columns == 0:
            continue
        padded = [row + ["" for _ in range(max_columns - len(row))] for row in rows]
        dataframe = pd.DataFrame(padded)
        safe_title = sanitize_filename(worksheet.title)
        csv_path = os.path.join(csv_dir, f"{safe_title}.csv")
        dataframe.to_csv(csv_path, index=False, header=False)
        print(f"Wrote CSV for sheet '{worksheet.title}': {csv_path}")
