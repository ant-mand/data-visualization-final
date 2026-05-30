"""
Assesses whether HF visibility differs by modality and documentation conditions.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

import numpy as np
import pandas as pd


# --- PATHS ---

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

INPUT_CSV = os.path.join(PROJECT_ROOT, "data", "provenance.csv")

DERIVED_DIR = os.path.join(PROJECT_ROOT, "data", "derived")

VIS_BY_MODALITY_CSV = os.path.join(DERIVED_DIR, "visibility_by_modality.csv")
VIS_BY_DOCFLAG_CSV = os.path.join(DERIVED_DIR, "visibility_by_docflag.csv")
VIS_DATASET_DETAIL_CSV = os.path.join(DERIVED_DIR, "dataset_visibility_detail.csv")


# --- CONFIG ---

DOC_FLAGS: List[str] = [
    "has_license",
    "has_sources",
    "has_human_annotation",
]

# low / medium / high documentation buckets based on documentation_score_raw
DOC_SCORE_COL = "documentation_score_raw"
DOC_SCORE_BUCKET_COL = "doc_score_bucket"
DOC_SCORE_BUCKETS = ["low", "medium", "high"]


# --- HELPERS ---

def gini(values: pd.Series) -> float:
    """
    Gini coefficient (0 = perfect equality, 1 = maximum inequality).

    We treat hf_downloads as a non-negative visibility metric; higher Gini means
    downloads are more concentrated in a small subset of datasets.[web:273]
    """
    v = np.array([x for x in values if pd.notna(x) and x >= 0], dtype=float)
    if v.size == 0:
        return float("nan")
    v = np.sort(v)
    cum = np.cumsum(v)
    if cum[-1] == 0:
        return 0.0
    n = v.size
    return (n + 1 - 2 * np.sum(cum) / cum[-1]) / n


def dist_stats(s: pd.Series) -> Optional[Dict[str, float]]:
    """
    Basic distribution statistics for a non-negative series.
    """
    s = s.dropna()
    if s.empty:
        return None

    return {
        "n": float(len(s)),
        "median": float(s.median()),
        "p25": float(s.quantile(0.25)),
        "p75": float(s.quantile(0.75)),
        "p90": float(s.quantile(0.9)),
        "max": float(s.max()),
        "gini": float(gini(s)),
    }


def add_doc_score_buckets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add low / medium / high buckets based on documentation_score_raw tertiles.
    """
    if DOC_SCORE_COL not in df.columns:
        df[DOC_SCORE_BUCKET_COL] = "unknown"
        return df

    s = df[DOC_SCORE_COL].dropna()
    if s.empty:
        df[DOC_SCORE_BUCKET_COL] = "unknown"
        return df

    q1, q2 = s.quantile([0.33, 0.67])

    def bucket(x: float) -> str:
        if np.isnan(x):
            return "unknown"
        if x < q1:
            return "low"
        if x < q2:
            return "medium"
        return "high"

    df[DOC_SCORE_BUCKET_COL] = df[DOC_SCORE_COL].apply(bucket)
    return df


# --- MAIN ---

def main() -> None:
    if not os.path.isfile(INPUT_CSV):
        raise SystemExit(f"CSV not found: {INPUT_CSV}. Run build_dataset.py first.")

    os.makedirs(DERIVED_DIR, exist_ok=True)

    df = pd.read_csv(INPUT_CSV)

    required_cols = ["modality", "hf_downloads"] + DOC_FLAGS
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise SystemExit(
            f"Missing required columns in provenance.csv: {missing}. "
            "Make sure build_dataset.py and analysis_documentation.py are aligned."
        )

    df["modality"] = df["modality"].fillna("unknown").astype(str)
    df["hf_downloads"] = pd.to_numeric(df["hf_downloads"], errors="coerce")

    for flag in DOC_FLAGS:
        df[flag] = df[flag].fillna(0).astype(int)

    df = add_doc_score_buckets(df)

    # filter to datasets with download data
    df_attn = df[df["hf_downloads"].notna()].copy()

    # visibility by modality 
    rows_modality: List[Dict[str, float]] = []

    for modality, grp in df_attn.groupby("modality"):
        stats = dist_stats(grp["hf_downloads"])
        if stats is None:
            continue

        row = {
            "modality": modality,
            "n_with_downloads": stats["n"],
            "median_downloads": stats["median"],
            "p25_downloads": stats["p25"],
            "p75_downloads": stats["p75"],
            "p90_downloads": stats["p90"],
            "max_downloads": stats["max"],
            "gini_downloads": stats["gini"],
        }
        rows_modality.append(row)

    vis_by_modality = pd.DataFrame(rows_modality).sort_values("modality")
    vis_by_modality.to_csv(VIS_BY_MODALITY_CSV, index=False)

    # visibility by documentation flags
    rows_docflag: List[Dict[str, float]] = []

    for flag in DOC_FLAGS:
        flag_label = flag  # can prettify in the dashboard layer

        for (modality, flag_val), grp in df_attn.groupby(["modality", flag]):
            stats = dist_stats(grp["hf_downloads"])
            if stats is None:
                continue

            rows_docflag.append(
                {
                    "modality": modality,
                    "doc_flag": flag,
                    "doc_flag_label": flag_label,
                    "doc_flag_value": int(flag_val),
                    "n_with_downloads": stats["n"],
                    "median_downloads": stats["median"],
                    "p25_downloads": stats["p25"],
                    "p75_downloads": stats["p75"],
                    "p90_downloads": stats["p90"],
                    "max_downloads": stats["max"],
                    "gini_downloads": stats["gini"],
                }
            )

    # visibility by documentation-score bucket
    if DOC_SCORE_BUCKET_COL in df_attn.columns:
        for (modality, bucket), grp in df_attn.groupby(["modality", DOC_SCORE_BUCKET_COL]):
            stats = dist_stats(grp["hf_downloads"])
            if stats is None:
                continue

            rows_docflag.append(
                {
                    "modality": modality,
                    "doc_flag": DOC_SCORE_BUCKET_COL,
                    "doc_flag_label": "documentation_score_bucket",
                    "doc_flag_value": bucket,
                    "n_with_downloads": stats["n"],
                    "median_downloads": stats["median"],
                    "p25_downloads": stats["p25"],
                    "p75_downloads": stats["p75"],
                    "p90_downloads": stats["p90"],
                    "max_downloads": stats["max"],
                    "gini_downloads": stats["gini"],
                }
            )

    vis_by_docflag = pd.DataFrame(rows_docflag)
    vis_by_docflag.to_csv(VIS_BY_DOCFLAG_CSV, index=False)

    # dataset-level detail table
    # keep only columns that are useful for plotting/debugging:
    keep_cols = [
        "id",
        "name",
        "modality",
        "hf_downloads",
        "log_downloads",
        DOC_SCORE_COL,
        DOC_SCORE_BUCKET_COL,
    ] + DOC_FLAGS

    keep_cols = [c for c in keep_cols if c in df.columns]
    dataset_detail = df_attn[keep_cols].copy()
    dataset_detail.to_csv(VIS_DATASET_DETAIL_CSV, index=False)


if __name__ == "__main__":
    main()
