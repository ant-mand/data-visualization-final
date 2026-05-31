
"""
Utilities for loading dashboard data and building shared dashboard components.
"""

from __future__ import annotations

import os
import textwrap
from typing import Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import html


COLORS: Dict[str, str] = {
    "background": "#ffffff",
    "surface": "#ffffff",
    "surface_alt": "#f2ebe3",
    "text": "#111111",
    "muted_text": "#111111",
    "border": "#ded6cc",
    "text_modality": "#9E003A",
    "speech_modality": "#2F009E",
    "video_modality": "#217D00",
    "accent": "#1f3a5f",
    "accent_2": "#b85c38",
    "accent_3": "#6b8e5a",
    "unspecified": "#9ca3af",
}

FONT_SANS = "'Source Sans 3', 'Helvetica Neue', Arial, sans-serif"

MODALITY_ORDER: List[str] = ["text", "speech", "video"]
LICENSE_ORDER: List[str] = [
    "Permissive",
    "Copyleft / Share-Alike",
    "Non-Commercial",
    "Model-Restricted",
    "Custom/Restricted",
    "Other",
    "Unspecified",
]

MODALITY_COLORS: Dict[str, str] = {
    "text": COLORS["text_modality"],
    "speech": COLORS["speech_modality"],
    "video": COLORS["video_modality"],
}

LICENSE_COLORS: Dict[str, str] = {
    "Permissive": "#315c8d",
    "Copyleft / Share-Alike": "#4f7cac",
    "Non-Commercial": "#b85c38",
    "Model-Restricted": "#7a3e65",
    "Custom/Restricted": "#8c5a2b",
    "Other": "#7b8794",
    "Unspecified": "#b8bfc7",
}


def wrap_axis_label(text: str, width: int = 18) -> str:
    return "<br>".join(textwrap.wrap(str(text), width=width, break_long_words=False))


def project_paths() -> Dict[str, str]:
    project_root = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(project_root, "data")
    derived_dir = os.path.join(data_dir, "derived")
    return {
        "project_root": project_root,
        "data_dir": data_dir,
        "derived_dir": derived_dir,
        "provenance": os.path.join(data_dir, "provenance.csv"),
        "documentation_by_modality": os.path.join(derived_dir, "documentation_by_modality.csv"),
        "documentation_long": os.path.join(derived_dir, "documentation_long.csv"),
        "licenses_by_modality": os.path.join(derived_dir, "licenses_by_modality.csv"),
        "licenses_raw_examples": os.path.join(derived_dir, "licenses_raw_examples.csv"),
        "visibility_by_modality": os.path.join(derived_dir, "visibility_by_modality.csv"),
        "visibility_by_docflag": os.path.join(derived_dir, "visibility_by_docflag.csv"),
        "dataset_visibility_detail": os.path.join(derived_dir, "dataset_visibility_detail.csv"),
        "policy_checklist_by_modality": os.path.join(derived_dir, "policy_checklist_by_modality.csv"),
        "policy_checklist_long": os.path.join(derived_dir, "policy_checklist_long.csv"),
        "policy_doc_scores": os.path.join(derived_dir, "policy_doc_scores.csv"),
    }


def load_csv(path: str) -> pd.DataFrame:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Required file not found: {path}")
    return pd.read_csv(path)


def load_data() -> Dict[str, pd.DataFrame]:
    paths = project_paths()
    return {
        "provenance": load_csv(paths["provenance"]),
        "documentation_by_modality": load_csv(paths["documentation_by_modality"]),
        "documentation_long": load_csv(paths["documentation_long"]),
        "licenses_by_modality": load_csv(paths["licenses_by_modality"]),
        "licenses_raw_examples": load_csv(paths["licenses_raw_examples"]),
        "visibility_by_modality": load_csv(paths["visibility_by_modality"]),
        "visibility_by_docflag": load_csv(paths["visibility_by_docflag"]),
        "dataset_visibility_detail": load_csv(paths["dataset_visibility_detail"]),
        "policy_checklist_by_modality": load_csv(paths["policy_checklist_by_modality"]),
        "policy_checklist_long": load_csv(paths["policy_checklist_long"]),
        "policy_doc_scores": load_csv(paths["policy_doc_scores"]),
    }


def metric_card(card_id: str, label: str, value: str, short_blurb: str) -> html.Div:
    return html.Div(
        id=f"{card_id}-card",
        className="metric-card",
        children=[
            html.Div(
                className="flip-card-inner",
                children=[
                    html.Div(
                        className="flip-card-front",
                        children=[
                            html.Div(label, className="metric-label"),
                            html.Div(str(value), className="metric-value"),
                        ],
                    ),
                    html.Div(
                        className="flip-card-back",
                        children=[
                            html.Div(label, className="metric-label"),
                            html.P(short_blurb, className="metric-back-text"),
                            html.Button(
                                "Read more",
                                id=f"{card_id}-more",
                                className="metric-read-more",
                                n_clicks=0,
                            ),
                        ],
                    ),
                ],
            )
        ],
    )


def section(title: str, description: str, children: List) -> html.Section:
    return html.Section(
        className="section",
        children=[
            html.H2(title),
            html.P(description, className="desc"),
            *children,
        ],
    )


def base_figure(fig: go.Figure, height: int = 460) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor=COLORS["surface"],
        plot_bgcolor=COLORS["surface"],
        font=dict(family=FONT_SANS, color=COLORS["text"], size=12),
        margin=dict(l=170, r=24, t=72, b=44),
        legend=dict(
            orientation="h",
            y=1.10,
            x=1,
            xanchor="right",
            yanchor="bottom",
            traceorder="reversed",
            font=dict(family=FONT_SANS, size=11),
        ),
        transition=dict(duration=300, easing="cubic-in-out"),
    )
    fig.update_xaxes(showgrid=False, linecolor=COLORS["border"], automargin=True)
    fig.update_yaxes(
        gridcolor=COLORS["border"],
        zeroline=False,
        linecolor=COLORS["border"],
        automargin=False,
    )
    return fig


def split_multi_value(series: pd.Series) -> pd.Series:
    return (
        series.fillna("")
        .astype(str)
        .str.split(r"[|;,]")
        .explode()
        .str.strip()
    )


def top_terms_figure(df: pd.DataFrame, column: str, modality: str, title: str, top_n: int = 12) -> go.Figure:
    d = df[df["modality"] == modality].copy()
    values = split_multi_value(d[column])
    values = values[(values != "") & (values.str.lower() != "nan")]
    counts = values.value_counts().head(top_n).reset_index()
    counts.columns = ["label", "n_datasets"]
    counts = counts.sort_values("n_datasets", ascending=True)

    fig = px.bar(
        counts,
        x="n_datasets",
        y="label",
        orientation="h",
        labels={"n_datasets": "Datasets", "label": ""},
        title=title,
    )
    fig.update_traces(hovertemplate="Datasets: %{x}<extra></extra>", marker_line_width=0)
    fig.update_layout(bargap=0.18, showlegend=False, margin=dict(l=220, r=24, t=56, b=44))
    fig.update_yaxes(
        categoryorder="array",
        categoryarray=counts["label"].tolist(),
        tickfont=dict(size=11),
        ticks="outside",
        ticklen=4,
        ticklabelstandoff=8,
        fixedrange=True,
    )
    fig.update_xaxes(rangemode="tozero", fixedrange=True)
    return base_figure(fig, height=500)


def full_terms_figure(df: pd.DataFrame, column: str, modality: str, title: str) -> go.Figure:
    d = df[df["modality"] == modality].copy()
    values = split_multi_value(d[column])
    values = values[(values != "") & (values.str.lower() != "nan")]

    counts = values.value_counts().reset_index()
    counts.columns = ["label", "n_datasets"]
    counts = counts.sort_values(["n_datasets", "label"], ascending=[False, True]).copy()
    plot_counts = counts.iloc[::-1].copy()

    fig = px.bar(
        plot_counts,
        x="n_datasets",
        y="label",
        orientation="h",
        labels={"n_datasets": "Datasets", "label": ""},
        title=title,
    )
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>Datasets: %{x}<extra></extra>",
        marker_line_width=0,
    )
    fig.update_layout(bargap=0.12, showlegend=False, margin=dict(l=260, r=24, t=56, b=44))
    fig.update_yaxes(
        categoryorder="array",
        categoryarray=plot_counts["label"].tolist(),
        tickfont=dict(size=11),
        ticks="outside",
        ticklen=4,
        ticklabelstandoff=8,
        fixedrange=True,
    )
    fig.update_xaxes(rangemode="tozero", fixedrange=True)

    height = max(520, min(1400, 26 * len(plot_counts) + 120))
    return base_figure(fig, height=height)


def top_metrics(data: Dict[str, pd.DataFrame]) -> Dict[str, str]:
    df = data["provenance"]
    n_total = len(df)
    n_with_hf = int(df["hf_downloads"].notna().sum()) if "hf_downloads" in df.columns else 0
    modalities = ", ".join([m for m in MODALITY_ORDER if m in set(df["modality"].astype(str))])
    mean_doc = df["documentation_score_raw"].mean() if "documentation_score_raw" in df.columns else float("nan")

    modality_counts = df["modality"].fillna("unknown").astype(str).str.lower().value_counts()
    text_count = int(modality_counts.get("text", 0))
    speech_count = int(modality_counts.get("speech", 0))
    video_count = int(modality_counts.get("video", 0))

    return {
        "datasets": f"{n_total:,}",
        "modalities": modalities or "text, speech, video",
        "hf_data": f"{n_with_hf:,}",
        "mean_doc": f"{mean_doc:.2f}" if pd.notna(mean_doc) else "—",
        "dataset_breakdown": f"Text: {text_count:,} · Speech: {speech_count:,} · Video: {video_count:,}",
    }


def documentation_figure(doc_long: pd.DataFrame) -> go.Figure:
    field_order = [
        "Licenses",
        "Creators",
        "Sources",
        "Tasks",
        "Human Annotation Flag",
        "Parent Datasets",
        "Generating Models",
        "HF URL",
        "Paper URL",
        "Year",
    ]

    rename_map = {
        "License documented": "Licenses",
        "Creators documented": "Creators",
        "Sources documented": "Sources",
        "Tasks documented": "Tasks",
        "Human annotation flag documented": "Human Annotation Flag",
        "Parent datasets documented": "Parent Datasets",
        "Generating models documented": "Generating Models",
        "HF URL present": "HF URL",
        "Paper URL present": "Paper URL",
        "Year present": "Year",
    }

    d = doc_long.copy()
    d["field_label"] = d["field_label"].replace(rename_map)
    d = d[d["field_label"].isin(field_order)].copy()
    d["field_label"] = pd.Categorical(d["field_label"], categories=field_order, ordered=True)
    d["modality"] = pd.Categorical(d["modality"], categories=MODALITY_ORDER, ordered=True)
    d = d.sort_values(["field_label", "modality"]).copy()

    fig = px.bar(
        d,
        x="coverage_pct",
        y="field_label",
        color="modality",
        barmode="group",
        category_orders={
            "modality": MODALITY_ORDER,
            "field_label": field_order,
        },
        color_discrete_map=MODALITY_COLORS,
        labels={"coverage_pct": "Coverage (%)", "field_label": ""},
        custom_data=["modality", "field", "field_label", "n_datasets"],
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[2]}</b><br>"
            "Modality: %{customdata[0]}<br>"
            "Coverage: %{x:.1f}%<br>"
            "Datasets: %{customdata[3]}<extra></extra>"
        )
    )

    fig.update_layout(
        title="Documentation coverage",
        clickmode="event+select",
        yaxis={
            "categoryorder": "array",
            "categoryarray": field_order[::-1],
        },
    )

    return base_figure(fig, height=520)


def documentation_detail_figure(
    provenance: pd.DataFrame,
    licenses_by_modality: pd.DataFrame,
    modality: str,
    field: str,
    field_label: str,
) -> go.Figure:
    modality_color = MODALITY_COLORS.get(modality, COLORS["accent"])
    short_title = f"{modality.title()} — {field_label}"

    if field == "has_license":
        d = licenses_by_modality[licenses_by_modality["modality"] == modality].copy()
        d["license_bucket"] = pd.Categorical(d["license_bucket"], categories=LICENSE_ORDER, ordered=True)
        d = d.sort_values("pct_within_modality", ascending=True)

        fig = px.bar(
            d,
            x="pct_within_modality",
            y="license_bucket",
            orientation="h",
            labels={"pct_within_modality": "Share of documented licenses (%)", "license_bucket": ""},
            title=short_title,
        )
        fig.update_traces(
            marker_color=modality_color,
            marker_line_width=0,
            hovertemplate="<b>%{y}</b><br>Share: %{x:.1f}%<br>Datasets: %{customdata[0]}<extra></extra>",
            customdata=d[["n_datasets"]].to_numpy(),
        )
        fig.update_layout(showlegend=False, bargap=0.18, margin=dict(l=220, r=24, t=56, b=44))
        fig.update_yaxes(
            categoryorder="array",
            categoryarray=d["license_bucket"].astype(str).tolist(),
            tickfont=dict(size=11),
            ticks="outside",
            ticklen=4,
            ticklabelstandoff=8,
            fixedrange=True,
        )
        fig.update_xaxes(rangemode="tozero", ticksuffix="%", fixedrange=True)
        return base_figure(fig, height=520)

    if field == "has_creators":
        fig = full_terms_figure(provenance[provenance["has_creators"] == 1], "creators", modality, short_title)
        fig.update_traces(marker_color=modality_color)
        return fig

    if field == "has_sources":
        fig = top_terms_figure(provenance[provenance["has_sources"] == 1], "text_sources", modality, short_title)
        fig.update_traces(marker_color=modality_color)
        return fig

    if field == "has_tasks":
        fig = top_terms_figure(provenance[provenance["has_tasks"] == 1], "tasks", modality, short_title)
        fig.update_traces(marker_color=modality_color)
        return fig

    fig = go.Figure()
    fig.add_annotation(
        text=f"No detailed breakout is available yet for {field_label.lower()} in {modality}.",
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        align="center",
        font=dict(family=FONT_SANS, size=15, color=COLORS["muted_text"]),
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(
        title=short_title,
        paper_bgcolor=COLORS["surface"],
        plot_bgcolor=COLORS["surface"],
        margin=dict(l=40, r=24, t=56, b=24),
        height=420,
        transition=dict(duration=300, easing="cubic-in-out"),
        showlegend=False,
    )
    return fig


# def licenses_figure(licenses_by_modality: pd.DataFrame) -> go.Figure:
#     d = licenses_by_modality.copy()
#     d["license_bucket"] = pd.Categorical(d["license_bucket"], categories=LICENSE_ORDER, ordered=True)
#     fig = px.bar(
#         d,
#         x="modality",
#         y="pct_within_modality",
#         color="license_bucket",
#         barmode="stack",
#         category_orders={"modality": MODALITY_ORDER, "license_bucket": LICENSE_ORDER},
#         color_discrete_map=LICENSE_COLORS,
#         labels={"pct_within_modality": "Share within modality (%)", "modality": "Modality"},
#         hover_data={"n_datasets": True, "n_modality_total": True, "pct_within_modality": ":.1f"},
#     )
#     return base_figure(fig, height=430)


def raw_license_table(raw_examples: pd.DataFrame) -> pd.DataFrame:
    return raw_examples.sort_values(["modality", "rank"]).copy()


# def visibility_modality_figure(visibility_by_modality: pd.DataFrame) -> go.Figure:
#     fig = px.bar(
#         visibility_by_modality,
#         x="modality",
#         y="median_downloads",
#         color="modality",
#         category_orders={"modality": MODALITY_ORDER},
#         color_discrete_map=MODALITY_COLORS,
#         labels={"median_downloads": "Median HF downloads", "modality": "Modality"},
#         hover_data={
#             "n_with_downloads": True,
#             "p25_downloads": ":,.0f",
#             "p75_downloads": ":,.0f",
#             "p90_downloads": ":,.0f",
#             "max_downloads": ":,.0f",
#             "gini_downloads": ":.3f",
#         },
#     )
#     return base_figure(fig, height=420)


# def visibility_docflag_figure(visibility_by_docflag: pd.DataFrame, selected_flag: str) -> go.Figure:
#     d = visibility_by_docflag[visibility_by_docflag["doc_flag"] == selected_flag].copy()
#     if d.empty:
#         return base_figure(go.Figure(), height=420)

#     d["group_label"] = d["doc_flag_value"].astype(str).replace({
#         "0": "No",
#         "1": "Yes",
#         "low": "Low",
#         "medium": "Medium",
#         "high": "High",
#     })

#     fig = px.bar(
#         d,
#         x="modality",
#         y="median_downloads",
#         color="group_label",
#         barmode="group",
#         category_orders={"modality": MODALITY_ORDER},
#         labels={"median_downloads": "Median HF downloads", "modality": "Modality", "group_label": "Group"},
#         hover_data={
#             "n_with_downloads": True,
#             "p25_downloads": ":,.0f",
#             "p75_downloads": ":,.0f",
#             "p90_downloads": ":,.0f",
#             "gini_downloads": ":.3f",
#         },
#     )
#     return base_figure(fig, height=430)


# def policy_heatmap_figure(policy_long: pd.DataFrame) -> go.Figure:
#     field_order = [
#         "Identifier present (id/name/modality)",
#         "Public link present (HF or paper)",
#         "Source information present",
#         "License information present",
#         "Creator information present",
#         "Annotation information present",
#         "Parent dataset references present",
#         "Generating model references present",
#         "Task information present",
#         "Year/date present",
#     ]
#     d = policy_long.copy()
#     d["field_label"] = pd.Categorical(d["field_label"], categories=field_order, ordered=True)
#     pivot = (
#         d.pivot(index="field_label", columns="modality", values="coverage_pct")
#         .reindex(index=field_order, columns=[m for m in MODALITY_ORDER if m in d["modality"].unique()])
#     )

#     fig = go.Figure(
#         data=go.Heatmap(
#             z=pivot.values,
#             x=list(pivot.columns),
#             y=list(pivot.index),
#             colorscale=[
#                 [0.0, "#f3efe9"],
#                 [0.25, "#d9e4f0"],
#                 [0.5, "#9bb9d6"],
#                 [0.75, "#5f88b3"],
#                 [1.0, "#315c8d"],
#             ],
#             zmin=0,
#             zmax=100,
#             colorbar=dict(title="Coverage %"),
#             hovertemplate="Field: %{y}<br>Modality: %{x}<br>Coverage: %{z:.1f}%<extra></extra>",
#         )
#     )
#     return base_figure(fig, height=520)


# def policy_score_figure(policy_scores: pd.DataFrame) -> go.Figure:
#     d = policy_scores.groupby("modality", as_index=False)["policy_doc_score"].mean().sort_values("modality")
#     fig = px.bar(
#         d,
#         x="modality",
#         y="policy_doc_score",
#         color="modality",
#         category_orders={"modality": MODALITY_ORDER},
#         color_discrete_map=MODALITY_COLORS,
#         labels={"policy_doc_score": "Mean policy documentation score", "modality": "Modality"},
#     )
#     fig.update_yaxes(range=[0, 1])
#     return base_figure(fig, height=400)
