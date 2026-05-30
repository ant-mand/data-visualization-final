"""
Translates observable metadata fields into a policy-relevant documentation checklist.

AI DISCLOSURE: Perplexity helped me write this code.
"""

from __future__ import annotations

import os
from typing import Dict, List

import pandas as pd


# --- PATHS ---

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

INPUT_CSV = os.path.join(PROJECT_ROOT, "data", "provenance.csv")

DERIVED_DIR = os.path.join(PROJECT_ROOT, "data", "derived")

POLICY_BY_MODALITY_CSV = os.path.join(DERIVED_DIR, "policy_checklist_by_modality.csv")
POLICY_LONG_CSV = os.path.join(DERIVED_DIR, "policy_checklist_long.csv")
POLICY_SCORES_CSV = os.path.join(DERIVED_DIR, "policy_doc_scores.csv")


# --- CONFIG ---

CHECKLIST_FIELDS: List[str] = [
    "has_identifier",         # id + name + modality info present
    "has_link",               # at least one public URL (HF or paper) present
    "has_sources",            # text sources / source info present
    "has_license",            # some license string present
    "has_creators",           # creators present
    "has_human_annotation",   # human annotation information present
    "has_parent_refs",        # parent/provenance references present
    "has_generating_models",  # generating model(s) referenced
    "has_tasks",              # task information present
    "has_year",               # year present
]

CHECKLIST_LABELS: Dict[str, str] = {
    "has_identifier": "Identifier present (id/name/modality)",
    "has_link": "Public link present (HF or paper)",
    "has_sources": "Source information present",
    "has_license": "License information present",
    "has_creators": "Creator information present",
    "has_human_annotation": "Annotation information present",
    "has_parent_refs": "Parent dataset references present",
    "has_generating_models": "Generating model references present",
    "has_tasks": "Task information present",
    "has_year": "Year/date present",
}


# --- HELPERS ---

def has_content(value: object) -> bool:
    """
    Return True when a string-like value contains non-empty content.
    """
    return isinstance(value, str) and bool(value.strip())


# --- MAIN ---

def main() -> None:
    if not os.path.isfile(INPUT_CSV):
        raise SystemExit(f"CSV not found: {INPUT_CSV}. Run build_dataset.py first.")

    os.makedirs(DERIVED_DIR, exist_ok=True)

    df = pd.read_csv(INPUT_CSV)

    base_required = [
        "id",
        "name",
        "modality",
        "has_sources",
        "has_license",
        "has_creators",
        "has_human_annotation",
        "has_parent_refs",
        "has_generating_models",
        "has_tasks",
        "has_year",
        "hf_url",
        "arxiv_url",
    ]
    missing = [c for c in base_required if c not in df.columns]
    if missing:
        raise SystemExit(
            f"Missing required columns in provenance.csv: {missing}. "
            "Make sure build_dataset.py is up to date."
        )

    df["modality"] = df["modality"].fillna("unknown").astype(str)

    # build dataset-level checklist flags
    has_identifier = df["id"].apply(has_content) | df["name"].apply(has_content)
    has_link = df["hf_url"].apply(has_content) | df["arxiv_url"].apply(has_content)

    df["has_identifier"] = has_identifier.astype(int)
    df["has_link"] = has_link.astype(int)

    # ensure existing flags are 0/1 ints
    for col in [
        "has_sources",
        "has_license",
        "has_creators",
        "has_human_annotation",
        "has_parent_refs",
        "has_generating_models",
        "has_tasks",
        "has_year",
    ]:
        df[col] = df[col].fillna(0).astype(int)

    # per-dataset policy_doc_score = fraction of checklist fields present
    df["policy_fields_present"] = df[CHECKLIST_FIELDS].sum(axis=1).astype(int)
    df["policy_fields_possible"] = len(CHECKLIST_FIELDS)
    df["policy_doc_score"] = df["policy_fields_present"] / df["policy_fields_possible"]

    policy_scores = df[
        ["id", "name", "modality", "policy_fields_present", "policy_fields_possible", "policy_doc_score"]
        + CHECKLIST_FIELDS
    ].copy()
    policy_scores.to_csv(POLICY_SCORES_CSV, index=False)

    # coverage by modality
    modality_counts = (
        df.groupby("modality")
        .size()
        .rename("n_datasets")
        .reset_index()
    )

    coverage = (
        df.groupby("modality")[CHECKLIST_FIELDS]
        .mean()
        .reset_index()
    )
    for col in CHECKLIST_FIELDS:
        coverage[col] = (coverage[col] * 100.0).round(2)

    policy_by_modality = modality_counts.merge(coverage, on="modality", how="left")
    policy_by_modality.to_csv(POLICY_BY_MODALITY_CSV, index=False)

    rows_long: List[Dict[str, object]] = []

    for _, row in policy_by_modality.iterrows():
        modality = row["modality"]
        n_datasets = int(row["n_datasets"])
        for field in CHECKLIST_FIELDS:
            rows_long.append(
                {
                    "modality": modality,
                    "field": field,
                    "field_label": CHECKLIST_LABELS.get(field, field),
                    "n_datasets": n_datasets,
                    "coverage_pct": float(row[field]),
                }
            )

    policy_long = pd.DataFrame(rows_long)
    policy_long.to_csv(POLICY_LONG_CSV, index=False)


if __name__ == "__main__":
    main()
