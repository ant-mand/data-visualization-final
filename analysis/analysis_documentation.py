"""
This script analyzes the fields in the data summaries --
* what fields are documented by modality?
* how do source/creator/annotation practices differ across modality?
"""

from __future__ import annotations

import os
from typing import List

import pandas as pd
import numpy as np


# --- PATHS ---

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

INPUT_CSV = os.path.join(PROJECT_ROOT, "data", "provenance.csv")

DERIVED_DIR = os.path.join(PROJECT_ROOT, "data", "derived")

DOC_BY_MODALITY_CSV = os.path.join(DERIVED_DIR, "documentation_by_modality.csv")
DOC_LONG_CSV = os.path.join(DERIVED_DIR, "documentation_long.csv")


# --- CONFIG ---

DOC_FIELDS: List[str] = [
    "has_license",
    "has_creators",
    "has_sources",
    "has_tasks",
    "has_human_annotation",
    "has_parent_refs",
    "has_generating_models",
    "has_hf_url",
    "has_arxiv_url",
    "has_year",
]

DOC_LABELS = {
    "has_license": "License documented",
    "has_creators": "Creators documented",
    "has_sources": "Sources documented",
    "has_tasks": "Tasks documented",
    "has_human_annotation": "Human annotation flag documented",
    "has_parent_refs": "Parent datasets documented",
    "has_generating_models": "Generating models documented",
    "has_hf_url": "HF URL present",
    "has_arxiv_url": "Paper URL present",
    "has_year": "Year present",
}


# --- MAIN ---

def main() -> None:
    if not os.path.isfile(INPUT_CSV):
        raise SystemExit(f"CSV not found: {INPUT_CSV}. Run build_dataset.py first.")

    os.makedirs(DERIVED_DIR, exist_ok=True)

    df = pd.read_csv(INPUT_CSV)

    # Basic sanity checks
    if "modality" not in df.columns:
        raise SystemExit("Expected 'modality' column in provenance.csv but did not find it.")

    missing_flags = [f for f in DOC_FIELDS if f not in df.columns]
    if missing_flags:
        raise SystemExit(
            f"Missing documentation flag columns in provenance.csv: {missing_flags}. "
            "Make sure build_dataset.py is up to date."
        )

    # flags must be 0/1 ints
    for col in DOC_FIELDS:
        df[col] = df[col].fillna(0).astype(int)

    # count of datasets per modality
    modality_counts = df.groupby("modality").size().rename("n_datasets").reset_index()

    # mean for each doc field by modality
    coverage = (
        df.groupby("modality")[DOC_FIELDS]
        .mean()
        .reset_index()
    )
    # convert to percentages
    for col in DOC_FIELDS:
        coverage[col] = coverage[col] * 100.0

    doc_by_modality = modality_counts.merge(coverage, on="modality", how="left")

    # write table
    doc_by_modality.to_csv(DOC_BY_MODALITY_CSV, index=False)

    # one row per (modality, field)
    long_rows = []

    for _, row in doc_by_modality.iterrows():
        modality = row["modality"]
        n_datasets = int(row["n_datasets"])
        for field in DOC_FIELDS:
            long_rows.append(
                {
                    "modality": modality,
                    "field": field,
                    "field_label": DOC_LABELS.get(field, field),
                    "n_datasets": n_datasets,
                    "coverage_pct": float(row[field]),
                }
            )

    doc_long = pd.DataFrame(long_rows)
    doc_long.to_csv(DOC_LONG_CSV, index=False)


if __name__ == "__main__":
    main()
