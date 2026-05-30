"""Build dash app."""

from dash import Dash, Input, Output, State, dcc, html, dash_table, callback_context
from dash_extensions import EventListener

from dashboard_utils import (
    documentation_detail_figure,
    documentation_figure,
    load_data,
    metric_card,
    policy_heatmap_figure,
    policy_score_figure,
    raw_license_table,
    section,
    top_metrics,
    visibility_docflag_figure,
    visibility_modality_figure,
)

app = Dash(__name__, title="Multimodal Dataset Provenance Dashboard")
server = app.server

data = load_data()
metrics = top_metrics(data)
license_table_df = raw_license_table(data["licenses_raw_examples"])

app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;500;600;700&display=swap" rel="stylesheet">
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""

hover_events = [
    {"event": "mouseenter", "props": ["type"]},
    {"event": "mouseleave", "props": ["type"]},
]


def wrapped_metric_card(card_id, label, value, short_blurb):
    return html.Div(
        className="metric-card-wrap",
        children=[
            EventListener(
                id=f"{card_id}-listener",
                events=hover_events,
                logging=False,
                children=metric_card(card_id, label, value, short_blurb),
            )
        ],
    )


app.layout = html.Div(
    className="app-shell",
    children=[
        dcc.Store(id="hovered-card-store", data=""),
        dcc.Store(id="active-metric-store", data=""),
        dcc.Store(id="documentation-view-store", data=None),
        html.Div(
            className="hero-wrap",
            children=[
                html.Section(
                    className="section hero-section",
                    children=[
                        html.H1("Multimodal Dataset Provenance Dashboard"),
                        html.P(
                            "This dashboard analyses data available from the Data Provenance Initiative, which is linked below. "
                            "It explores how openly available text, speech, and video datasets describe where their data comes from and how they can be used. "
                            "It summarizes documentation coverage for key fields like licenses, creators, sources, and tasks, and compares how these patterns differ across modalities. "
                            "The goal is to give practitioners and policymakers a quick way to understand the dataset produced by the initiative, which will help answer questions related to the ecosystem's transparency and responsible AI development."
                        ),
                    ],
                ),
                html.Section(
                    className="section hero-section",
                    children=[
                        html.H2("What is data provenance?"),
                        html.P(
                            "Data provenance describes the “story” of a dataset: where its contents came from, how they were collected or generated, how they were transformed, and under what terms they can be used. "
                            "Provenance includes not just web domains or platforms (like Wikipedia or YouTube), but also licensing, geographic and linguistic coverage, human annotation, and relationships between derived datasets and their sources. "
                            "Provenance makes it possible to trace training data back to its origins, assess legal and ethical risks, and understand over- or under-represented data in AI systems. "
                            "Weak or missing provenance may obscure restrictions, amplify existing skews in who is represented, and make it harder to build accountable and inclusive models."
                        ),
                        html.P([
                            "In order to address this problem, the Data Provenance Initiative ",
                            html.Strong("audited over 1800 datasets"),
                            ", tracing their sources, licenses, creators, and uses, and released an open dataset and interactive Explorer tool so practitioners can filter, inspect, and document training data with much stronger accountability.",
                        ]),
                        html.Div(
                            html.A(
                                "Visit the Data Provenance Initiative",
                                href="https://www.dataprovenance.org/",
                                target="_blank",
                                rel="noopener noreferrer",
                                className="hero-button",
                            ),
                            style={"display": "flex", "justifyContent": "center", "marginTop": "18px"},
                        ),
                        html.Br(),
                        html.Br(),
                        html.H2("Our Goal"),
                        html.P(
                            "We extend their work by comparing provenance across modalities. We look at where documentation is strongest and which policy-relevant fields are missing or underspecified in the dataset records."
                        ),
                    ],
                ),
                html.Section(
                    className="section hero-section",
                    children=[
                        html.H2("Dataset overview"),
                        html.Div(
                            className="hero-metrics",
                            children=[
                                html.Div(
                                    className="metrics-grid",
                                    children=[
                                        wrapped_metric_card(
                                            "datasets",
                                            "# of Dataset Records Audited",
                                            metrics["datasets"],
                                            "# of dataset records analyzed.",
                                        ),
                                        wrapped_metric_card(
                                            "hfdata",
                                            "# of datasets with Hugging Face (HF) download data",
                                            metrics["hf_data"],
                                            "# of datasets with data on HF downloads.",
                                        ),
                                        wrapped_metric_card(
                                            "modalities",
                                            "Modalities Represented",
                                            metrics["modalities"],
                                            "Modalities represented in the dataset.",
                                        ),
                                        wrapped_metric_card(
                                            "datasetbreakdown",
                                            "Dataset records by modality",
                                            metrics["dataset_breakdown"],
                                            "Count of audited dataset records for text, speech, and video.",
                                        ),
                                    ],
                                ),
                                html.Div(
                                    id="metric-detail-panel",
                                    className="metric-detail-panel hidden",
                                    children=[],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        section(
            "Documentation coverage",
            "Click a bar to drill into what is documented for that modality and field.",
            [
                html.Div(
                    className="controls-row",
                    children=[
                        html.Button(
                            "Back to coverage",
                            id="documentation-back-button",
                            n_clicks=0,
                            style={"display": "none"},
                            className="hero-button",
                        ),
                        html.Div(
                            id="documentation-view-title",
                            className="detail-subhead",
                            children="Coverage of documented fields across modalities.",
                        ),
                    ],
                ),
                dcc.Graph(
                    id="documentation-chart",
                    figure=documentation_figure(data["documentation_long"]),
                    config={"displayModeBar": False, "scrollZoom": False},
                ),
                html.Div(id="documentation-detail-table-wrap", children=[]),
            ],
        ),
        section(
            "Platform visibility",
            "These charts use Hugging Face downloads as a platform visibility measure and compare visibility across modalities and documentation conditions.",
            [
                dcc.Graph(
                    figure=visibility_modality_figure(data["visibility_by_modality"]),
                    config={"displayModeBar": False, "scrollZoom": False},
                ),
                html.Div(
                    className="controls-row",
                    children=[
                        html.Label("Compare visibility by documentation condition:"),
                        dcc.Dropdown(
                            id="doc-flag-dropdown",
                            options=[
                                {"label": "License present", "value": "has_license"},
                                {"label": "Sources present", "value": "has_sources"},
                                {"label": "Human annotation present", "value": "has_human_annotation"},
                                {"label": "Documentation score bucket", "value": "doc_score_bucket"},
                            ],
                            value="has_sources",
                            clearable=False,
                            style={"width": "320px"},
                        ),
                    ],
                ),
                dcc.Graph(
                    id="visibility-docflag-figure",
                    config={"displayModeBar": False, "scrollZoom": False},
                ),
            ],
        ),
        section(
            "Policy-relevant gaps",
            "This section translates observable metadata into a policy-relevant checklist. It shows which documentation facts are visible, not whether datasets are legally compliant.",
            [
                dcc.Graph(
                    figure=policy_heatmap_figure(data["policy_checklist_long"]),
                    config={"displayModeBar": False, "scrollZoom": False},
                ),
                dcc.Graph(
                    figure=policy_score_figure(data["policy_doc_scores"]),
                    config={"displayModeBar": False, "scrollZoom": False},
                ),
            ],
        ),
    ],
)


@app.callback(
    Output("documentation-view-store", "data"),
    Input("documentation-chart", "clickData"),
    Input("documentation-back-button", "n_clicks"),
    State("documentation-view-store", "data"),
    prevent_initial_call=True,
)
def set_documentation_view(click_data, back_clicks, current_view):
    triggered = callback_context.triggered[0]["prop_id"].split(".")[0]

    if triggered == "documentation-back-button":
        return None

    if triggered == "documentation-chart":
        if not click_data or "points" not in click_data:
            return current_view

        point = click_data["points"][0]
        return {
            "modality": point["customdata"][0],
            "field": point["customdata"][1],
            "field_label": point["customdata"][2],
        }

    return current_view


@app.callback(
    Output("documentation-chart", "figure"),
    Output("documentation-view-title", "children"),
    Output("documentation-back-button", "style"),
    Output("documentation-detail-table-wrap", "children"),
    Input("documentation-view-store", "data"),
)
def render_documentation_view(view_state):
    if not view_state:
        return (
            documentation_figure(data["documentation_long"]),
            "Coverage of documented fields across modalities.",
            {"display": "none"},
            [],
        )

    modality = view_state["modality"]
    field = view_state["field"]
    field_label = view_state["field_label"]

    fig = documentation_detail_figure(
        data["provenance"],
        data["licenses_by_modality"],
        modality,
        field,
        field_label,
    )

    table = []
    if field == "has_license":
        filtered = license_table_df[license_table_df["modality"] == modality].copy()
        table = [
            dash_table.DataTable(
                columns=[
                    {"name": "Rank", "id": "rank"},
                    {"name": "Raw license", "id": "raw_license"},
                    {"name": "Count", "id": "count"},
                    {"name": "% within raw mentions", "id": "pct_within_raw_mentions"},
                ],
                data=filtered.to_dict("records"),
                page_size=8,
                sort_action="native",
                style_table={"overflowX": "auto", "marginTop": "8px"},
                style_cell={
                    "textAlign": "left",
                    "padding": "10px",
                    "fontFamily": "Source Sans 3, Helvetica Neue, Arial, sans-serif",
                    "fontSize": "13px",
                    "backgroundColor": "#fffdf9",
                    "border": "1px solid #ded6cc",
                    "whiteSpace": "normal",
                    "height": "auto",
                },
                style_header={
                    "backgroundColor": "#f2ebe3",
                    "fontWeight": "600",
                    "border": "1px solid #ded6cc",
                },
            )
        ]

    return (
        fig,
        f"{modality.title()} · {field_label}",
        {"display": "inline-flex"},
        table,
    )


@app.callback(
    Output("hovered-card-store", "data"),
    Input("datasets-listener", "event"),
    Input("modalities-listener", "event"),
    Input("hfdata-listener", "event"),
    Input("datasetbreakdown-listener", "event"),
    prevent_initial_call=True,
)
def track_hover(datasets_event, modalities_event, hfdata_event, datasetbreakdown_event):
    triggered = callback_context.triggered
    if not triggered:
        return ""

    trigger_id = triggered[0]["prop_id"].split(".")[0]
    event = {
        "datasets-listener": datasets_event,
        "modalities-listener": modalities_event,
        "hfdata-listener": hfdata_event,
        "datasetbreakdown-listener": datasetbreakdown_event,
    }.get(trigger_id)

    card_map = {
        "datasets-listener": "datasets",
        "modalities-listener": "modalities",
        "hfdata-listener": "hfdata",
        "datasetbreakdown-listener": "datasetbreakdown",
    }

    if not event:
        return ""

    event_type = event.get("type", "")
    if event_type == "mouseenter":
        return card_map.get(trigger_id, "")
    if event_type == "mouseleave":
        return ""
    return ""


@app.callback(
    Output("active-metric-store", "data"),
    Input("datasets-more", "n_clicks"),
    Input("modalities-more", "n_clicks"),
    Input("hfdata-more", "n_clicks"),
    Input("datasetbreakdown-more", "n_clicks"),
    prevent_initial_call=True,
)
def set_active_metric(datasets_more, modalities_more, hfdata_more, datasetbreakdown_more):
    triggered = callback_context.triggered
    if not triggered:
        return ""

    trigger_id = triggered[0]["prop_id"].split(".")[0]
    mapping = {
        "datasets-more": "datasets",
        "modalities-more": "modalities",
        "hfdata-more": "hfdata",
        "datasetbreakdown-more": "datasetbreakdown",
    }
    return mapping.get(trigger_id, "")


@app.callback(
    Output("metric-detail-panel", "children"),
    Output("metric-detail-panel", "className"),
    Output("datasets-card", "className"),
    Output("modalities-card", "className"),
    Output("hfdata-card", "className"),
    Output("datasetbreakdown-card", "className"),
    Input("active-metric-store", "data"),
    Input("hovered-card-store", "data"),
)
def update_metric_detail(active_metric, hovered_card):
    base_classes = {
        "datasets": "metric-card",
        "modalities": "metric-card",
        "hfdata": "metric-card",
        "datasetbreakdown": "metric-card",
    }

    if not active_metric or hovered_card != active_metric:
        return (
            [],
            "metric-detail-panel hidden",
            base_classes["datasets"],
            base_classes["modalities"],
            base_classes["hfdata"],
            base_classes["datasetbreakdown"],
        )

    flipped_classes = base_classes.copy()
    flipped_classes[active_metric] = "metric-card is-flipped"

    details = {
        "datasets": [
            html.H3("Datasets"),
            html.P(
                "This metric reports the total number of dataset records included in the dashboard corpus. "
                "Because the analysis covers thousands of records, the patterns shown here should be interpreted as broad documentation tendencies rather than isolated examples."
            ),
        ],
        "modalities": [
            html.H3("Modalities"),
            html.P(
                "The dataset includes three modalities: text, speech, and video. "
                "Documentation norms may differ by data type."
            ),
        ],
        "hfdata": [
            html.H3("With HF download data"),
            html.P(
                "This metric shows how many dataset records have observable Hugging Face download counts available. "
                "Those counts are used here as one practical visibility signal."
                "This should not be treated as a measure of quality or fairness. Instead, it indicates which datasets are more visible or more actively circulating on a major platform."
            ),
        ],
        "datasetbreakdown": [
            html.H3("Dataset records by modality"),
            html.P(
                "This metric breaks the audited corpus into text, speech, and video records. "
            ),
            html.P(
                f"The current breakdown is {metrics['dataset_breakdown']}."
            ),
        ],
    }

    return (
        details[active_metric],
        "metric-detail-panel",
        flipped_classes["datasets"],
        flipped_classes["modalities"],
        flipped_classes["hfdata"],
        flipped_classes["datasetbreakdown"],
    )


@app.callback(
    Output("visibility-docflag-figure", "figure"),
    Input("doc-flag-dropdown", "value"),
)
def update_visibility_docflag(selected_flag: str):
    return visibility_docflag_figure(data["visibility_by_docflag"], selected_flag)


if __name__ == "__main__":
    app.run(debug=True)
