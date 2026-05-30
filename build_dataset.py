"""
Build the dataset for analysis.
-- HF = Hugging Face
AI DISCLOSURE: docstrings drafted with Perplexity, typing annotations revised with Perplexity.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, TypedDict, Union, cast
import json
import os

import numpy as np
import pandas as pd


# --- PATHS ---
PROJECT_ROOT: str = os.path.dirname(os.path.abspath(__file__))
DATA_PROVENANCE_ROOT: str = os.path.join(PROJECT_ROOT, "Data-Provenance-Collection")
OUTPUT_CSV: str = os.path.join(PROJECT_ROOT, "data", "provenance.csv")

SUMMARY_SOURCES: List[Tuple[str, str]] = [
    (os.path.join(DATA_PROVENANCE_ROOT, "data_summaries"), "text"),
    (os.path.join(DATA_PROVENANCE_ROOT, "data_summaries_speech"), "speech"),
    (os.path.join(DATA_PROVENANCE_ROOT, "data_summaries_video"), "video"),
]


# --- TYPES ---

Numeric = Union[int, float]
ScalarOrListStr = Union[str, List[str], None]

LicenseEntry = TypedDict(
    "LicenseEntry",
    {
        "License": str,
        "License URL": str,
    },
    total=False,
)

InferredMetadata = TypedDict(
    "InferredMetadata",
    {
        "HF Date": str,
        "S2 Date": str,
        "PwC Date": str,
        "Github Date": str,
        "HF Downloads (May 2024)": Numeric,
        "HF Likes (May 2024)": Numeric,
        "GitHub Stars (May 2024)": Numeric,
        "S2 Citation Count (May 2024)": Numeric,
        "HF Downloads (September 2023)": Numeric,
        "S2 Citation Count (September 2023)": Numeric,
    },
    total=False,
)

RawDatasetRecord = TypedDict(
    "RawDatasetRecord",
    {
        "Unique Dataset Identifier": ScalarOrListStr,
        "Dataset Name": ScalarOrListStr,
        "Paper Title": ScalarOrListStr,
        "Dataset URL": ScalarOrListStr,
        "GitHub URL": ScalarOrListStr,
        "Hugging Face URL": ScalarOrListStr,
        "Papers with Code URL": ScalarOrListStr,
        "ArXiv URL": ScalarOrListStr,
        "Semantic Scholar Corpus ID": Union[int, str],
        "Collection": ScalarOrListStr,
        "Collection URL": ScalarOrListStr,
        "Languages": Union[List[str], str],
        "Task Categories": Union[List[str], str],
        "Text Sources": Union[List[str], str],
        "Model Generated": Union[List[str], str],
        "Format": Union[List[str], str],
        "Human Annotation": ScalarOrListStr,
        "Derived from Datasets": Union[List[str], str],
        "Creators": Union[List[str], str],
        "Licenses": List[LicenseEntry],
        "License Notes": ScalarOrListStr,
        "License Verified By": ScalarOrListStr,
        "Dataset Filter IDs": Union[List[str], str],
        "Bibtex": ScalarOrListStr,
        "Inferred Metadata": InferredMetadata,
    },
    total=False,
)


class OutputRow(TypedDict):
    id: str
    name: str
    collection: str
    modality: str
    year: Optional[int]
    origin_mode: str
    has_model_signal: bool
    has_derivation_signal: bool
    has_original_tag: bool
    has_source_signal: bool
    all_licenses: str
    license_bucket: str
    creators: str
    languages: str
    text_sources: str
    tasks: str
    human_annotation: str
    format: str
    derived_from: str
    n_parents: int
    n_languages: int
    n_text_sources: int
    n_tasks: int
    generating_models: str
    n_generating_models: int
    hf_downloads: Optional[float]
    log_downloads: float
    hf_url: str
    arxiv_url: str
    paper_title: str
    has_license: int
    has_creators: int
    has_sources: int
    has_tasks: int
    has_human_annotation: int
    has_parent_refs: int
    has_generating_models: int
    has_hf_url: int
    has_arxiv_url: int
    has_year: int
    documentation_fields_count: int
    documentation_fields_possible: int
    documentation_score_raw: float


# --- CONSTANTS ---

LICENSE_RANK: Dict[str, int] = {
    "Unspecified": 0,
    "Other": 1,
    "Permissive": 2,
    "Copyleft / Share-Alike": 3,
    "Non-Commercial": 4,
    "Model-Restricted": 5,
    "Custom/Restricted": 6,
}


# --- HELPERS ---

def clean_string(value: ScalarOrListStr) -> str:
    """
    Normalize a scalar-like field into a clean string.
    If a list is present, join non-empty string items with '|'.
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        cleaned = [item.strip() for item in value if isinstance(item, str) and item.strip()]
        return "|".join(cleaned)
    return ""


def clean_string_list(value: Optional[Union[List[str], str]]) -> List[str]:
    """
    Normalize a string or list of strings into a clean list of non-empty strings.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    return []


def pipe_join(values: List[str]) -> str:
    """
    Join a list of strings into a pipe-delimited string.
    """
    return "|".join(values)


def get_year(infm: InferredMetadata) -> Optional[int]:
    """
    Pick the best available year from inferred metadata.
    """
    for key in ("HF Date", "S2 Date", "PwC Date", "Github Date"):
        date_str = infm.get(key)
        if isinstance(date_str, str) and len(date_str) >= 4 and date_str[:4].isdigit():
            return int(date_str[:4])
    return None


def get_origin_signals(rec: RawDatasetRecord) -> Dict[str, bool]:
    """
    Extract provenance signals from a raw dataset record.
    """
    model_gen = clean_string_list(rec.get("Model Generated"))
    derived = clean_string_list(rec.get("Derived from Datasets"))
    text_sources = clean_string_list(rec.get("Text Sources"))

    return {
        "has_model_signal": bool(model_gen),
        "has_derivation_signal": any(item != "original" for item in derived),
        "has_original_tag": "original" in derived,
        "has_source_signal": bool(text_sources),
    }


def get_origin_mode(rec: RawDatasetRecord) -> str:
    """
    Collapse provenance signals into one coarse origin label.
    """
    signals = get_origin_signals(rec)

    if signals["has_model_signal"]:
        return "model_generated"
    if signals["has_derivation_signal"]:
        return "dataset_derived"
    if signals["has_original_tag"]:
        return "original_source"
    if signals["has_source_signal"]:
        return "original_source"
    return "undocumented"


def license_summary(licenses: Optional[List[LicenseEntry]]) -> List[str]:
    """
    Return all non-empty reported license strings.
    """
    if not licenses:
        return []

    cleaned: List[str] = []
    for item in licenses:
        lic = item.get("License", "").strip()
        if lic:
            cleaned.append(lic)
    return cleaned


def bucket_single_license(lic: str) -> str:
    """
    Map one raw license string to a coarse restriction bucket.
    """
    normalized = lic.strip().lower()

    if not normalized or normalized in {"unspecified", "none", "unknown"}:
        return "Unspecified"

    if any(
        token in normalized
        for token in [
            "api",
            "terms",
            "eula",
            "custom",
            "proprietary",
            "google cloud translation",
        ]
    ):
        return "Custom/Restricted"

    if any(
        token in normalized
        for token in [
            "openai",
            "rail",
            "responsible ai",
            "use-based",
            "use restricted",
        ]
    ):
        return "Model-Restricted"

    if any(token in normalized for token in ["nc", "non-commercial"]):
        return "Non-Commercial"

    if any(token in normalized for token in ["by-sa", "share-alike", "share alike", "gpl"]):
        return "Copyleft / Share-Alike"

    if any(
        token in normalized
        for token in ["mit", "apache", "bsd", "cc0", "public domain", "cc by", "cc-by"]
    ):
        return "Permissive"

    return "Other"


def dataset_license_bucket(license_list: List[str]) -> str:
    """
    Assign the most restrictive bucket present in a dataset's reported licenses.
    """
    if not license_list:
        return "Unspecified"

    buckets = [bucket_single_license(lic) for lic in license_list]
    return max(buckets, key=lambda bucket: LICENSE_RANK[bucket])


def num(infm: InferredMetadata, key: str) -> Optional[float]:
    """
    Return a numeric inferred-metadata value if present.
    """
    value = infm.get(key)
    if isinstance(value, (int, float)):
        return float(value)
    return None


def has_content(value: str) -> bool:
    """
    Return True when a normalized string contains usable non-empty content.
    """
    return bool(value.strip())


# --- MAIN ---

def main() -> None:
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    rows: List[OutputRow] = []

    for summaries_dir, modality in SUMMARY_SOURCES:
        if not os.path.isdir(summaries_dir):
            print(f"Skipping missing summaries directory: {summaries_dir}")
            continue

        json_files: List[str] = sorted(
            file_name
            for file_name in os.listdir(summaries_dir)
            if file_name.endswith(".json") and not file_name.startswith("_")
        )
        print(f"Reading {len(json_files)} summaries from {summaries_dir} as {modality}")

        for file_name in json_files:
            file_path = os.path.join(summaries_dir, file_name)

            try:
                with open(file_path, "r", encoding="utf-8") as handle:
                    raw_data = json.load(handle)
                if not isinstance(raw_data, dict):
                    print(f"Skipping non-dict JSON root in {file_name}")
                    continue
                data = cast(Dict[str, RawDatasetRecord], raw_data)
            except Exception as exc:
                print(f"Failed to read file {file_name}: {exc}")
                continue

            for uid, rec in data.items():
                infm = rec.get("Inferred Metadata", {})
                license_names = license_summary(rec.get("Licenses"))
                origin_signals = get_origin_signals(rec)

                name = clean_string(rec.get("Dataset Name")) or uid
                collection = clean_string(rec.get("Collection"))
                human_annotation = clean_string(rec.get("Human Annotation"))
                hf_url = clean_string(rec.get("Hugging Face URL"))
                arxiv_url = clean_string(rec.get("ArXiv URL"))
                paper_title = clean_string(rec.get("Paper Title"))

                derived = clean_string_list(rec.get("Derived from Datasets"))
                model_gen = clean_string_list(rec.get("Model Generated"))
                creators = clean_string_list(rec.get("Creators"))
                languages = clean_string_list(rec.get("Languages"))
                sources = clean_string_list(rec.get("Text Sources"))
                tasks = clean_string_list(rec.get("Task Categories"))
                formats = clean_string_list(rec.get("Format"))

                creators_str = pipe_join(creators)
                languages_str = pipe_join(languages)
                sources_str = pipe_join(sources)
                tasks_str = pipe_join(tasks)
                formats_str = pipe_join(formats)
                derived_str = pipe_join(derived)
                model_gen_str = pipe_join(model_gen)

                hf_downloads = num(infm, "HF Downloads (May 2024)")
                log_downloads = (
                    float(np.log10(hf_downloads + 1))
                    if hf_downloads is not None and hf_downloads >= 0
                    else float("nan")
                )

                has_license = int(len(license_names) > 0)
                has_creators = int(has_content(creators_str))
                has_sources = int(has_content(sources_str))
                has_tasks = int(has_content(tasks_str))
                has_human_annotation = int(has_content(human_annotation))
                has_parent_refs = int(has_content(derived_str))
                has_generating_models = int(has_content(model_gen_str))
                has_hf_url = int(has_content(hf_url))
                has_arxiv_url = int(has_content(arxiv_url))
                year = get_year(infm)
                has_year = int(year is not None)

                documentation_fields: List[int] = [
                    has_license,
                    has_creators,
                    has_sources,
                    has_tasks,
                    has_human_annotation,
                    has_parent_refs,
                    has_generating_models,
                    has_hf_url,
                    has_arxiv_url,
                    has_year,
                ]
                documentation_fields_count = int(sum(documentation_fields))
                documentation_fields_possible = len(documentation_fields)
                documentation_score_raw = (
                    documentation_fields_count / documentation_fields_possible
                )

                row: OutputRow = {
                    #identity
                    "id": uid,
                    "name": name,
                    "collection": collection,
                    "modality": modality,
                    "year": year,

                    #provenance
                    "origin_mode": get_origin_mode(rec),
                    "has_model_signal": origin_signals["has_model_signal"],
                    "has_derivation_signal": origin_signals["has_derivation_signal"],
                    "has_original_tag": origin_signals["has_original_tag"],
                    "has_source_signal": origin_signals["has_source_signal"],
                    "all_licenses": pipe_join(license_names),
                    "license_bucket": dataset_license_bucket(license_names),
                    "creators": creators_str,
                    "languages": languages_str,
                    "text_sources": sources_str,
                    "tasks": tasks_str,
                    "human_annotation": human_annotation,
                    "format": formats_str,
                    "derived_from": derived_str,
                    "n_parents": len(derived),
                    "n_languages": len(languages),
                    "n_text_sources": len(sources),
                    "n_tasks": len(tasks),
                    "generating_models": model_gen_str,
                    "n_generating_models": len(model_gen),

                    #attention
                    "hf_downloads": hf_downloads,
                    "log_downloads": log_downloads,
                    "hf_url": hf_url,
                    "arxiv_url": arxiv_url,
                    "paper_title": paper_title,

                    #checks
                    "has_license": has_license,
                    "has_creators": has_creators,
                    "has_sources": has_sources,
                    "has_tasks": has_tasks,
                    "has_human_annotation": has_human_annotation,
                    "has_parent_refs": has_parent_refs,
                    "has_generating_models": has_generating_models,
                    "has_hf_url": has_hf_url,
                    "has_arxiv_url": has_arxiv_url,
                    "has_year": has_year,
                    "documentation_fields_count": documentation_fields_count,
                    "documentation_fields_possible": documentation_fields_possible,
                    "documentation_score_raw": documentation_score_raw,
                }

                rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Wrote {len(df)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
