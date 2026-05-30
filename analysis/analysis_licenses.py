"""
This script summarizes license distributions by modality.
We use the most restrictive license reported for each dataset to assign license_bucket
NOTE: we calculate dataset-level bucket shares, not shares of all raw license mentions.
"""

from __future__ import annotations

import os
from collections import Counter
from typing import List

import pandas as pd


# --- PATHS ---

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

INPUT_CSV = os.path.join(PROJECT_ROOT, "data", "provenance.csv")

DERIVED_DIR = os.path.join(PROJECT_ROOT, "data", "derived")

LICENSES_BY_MODALITY_CSV = os.path.join(DERIVED_DIR, "licenses_by_modality.csv")
LICENSES_RAW_EXAMPLES_CSV = os.path.join(DERIVED_DIR, "licenses_raw_examples.csv")


# --- CONFIG ---

LICENSE_BUCKET_ORDER: List[str] = [
    "Permissive",
    "Copyleft / Share-Alike",
    "Non-Commercial",
    "Model-Restricted",
    "Custom/Restricted",
    "Other",
    "Unspecified",
]


# --- HELPERS ---

def split_pipe(value: object) -> List[str]:
    """
    Split a pipe-delimited field into clean non-empty strings.
    """
    if not isinstance(value, str):
        return []
    return [part.strip() for part in value.split("|") if part.strip()]


def top_raw_license_examples(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Build a table of most common raw license strings per modality.
    """
    rows = []

    for modality, grp in df.groupby("modality"):
        counter: Counter[str] = Counter()

        for raw_value in grp["all_licenses"].fillna(""):
            licenses = split_pipe(raw_value)
            if licenses:
                counter.update(licenses)
            else:
                counter.update(["[no license reported]"])

        total = sum(counter.values())

        for rank, (license_string, count) in enumerate(counter.most_common(top_n), start=1):
            rows.append(
                {
                    "modality": modality,
                    "rank": rank,
                    "raw_license": license_string,
                    "count": int(count),
                    "pct_within_raw_mentions": round((count / total) * 100, 2) if total else 0.0,
                }
            )

    return pd.DataFrame(rows)


# --- MAIN ---

def main() -> None:
    if not os.path.isfile(INPUT_CSV):
        raise SystemExit(f"CSV not found: {INPUT_CSV}. Run build_dataset.py first.")

    os.makedirs(DERIVED_DIR, exist_ok=True)

    df = pd.read_csv(INPUT_CSV)

    required_cols = ["modality", "license_bucket", "all_licenses"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise SystemExit(
            f"Missing required columns in provenance.csv: {missing_cols}. "
            "Make sure build_dataset.py is up to date."
        )

    df["modality"] = df["modality"].fillna("unknown").astype(str)
    df["license_bucket"] = df["license_bucket"].fillna("Unspecified").astype(str)
    df["all_licenses"] = df["all_licenses"].fillna("").astype(str)

    # bucketed licenses

    counts = (
        df.groupby(["modality", "license_bucket"])
        .size()
        .reset_index(name="n_datasets")
    )

    modality_totals = (
        df.groupby("modality")
        .size()
        .reset_index(name="n_modality_total")
    )

    licenses_by_modality = counts.merge(modality_totals, on="modality", how="left")
    licenses_by_modality["pct_within_modality"] = (
        licenses_by_modality["n_datasets"] / licenses_by_modality["n_modality_total"] * 100.0
    ).round(2)

    licenses_by_modality["license_bucket"] = pd.Categorical(
        licenses_by_modality["license_bucket"],
        categories=LICENSE_BUCKET_ORDER,
        ordered=True,
    )

    licenses_by_modality = licenses_by_modality.sort_values(
        ["modality", "license_bucket"]
    ).reset_index(drop=True)

    licenses_by_modality.to_csv(LICENSES_BY_MODALITY_CSV, index=False)

    # raw license examples

    raw_examples = top_raw_license_examples(df, top_n=12)
    raw_examples.to_csv(LICENSES_RAW_EXAMPLES_CSV, index=False)


if __name__ == "__main__":
    main()
