import json

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import pandas as pd
import plotly.express as px

from dash import dash_table


DEFAULT_TO_DISPLAY = {
    "current_image_id": "None",
    "data": {
        "blurry": -1,
        "flash": -1,
        "relevant": -1,
        "valid": -1,
        "text": None,
        "shapes": [],
    },
}


def get_metadata_component(metadata: pd.DataFrame) -> dbc.Card:
    metadata["id"] = metadata["image_id"]
    metadata_columns = ["id", "image_id", "label", "source", "discrepancy"]
    # fmt: off
    table_columns = [
        {"name": "ImageID", "id": "image_id", "type": "text"},
        {"name": "Label", "id": "label", "type": "numeric"},
        {"name": "Source", "id": "source", "type": "text"},
        {"name": "Discrepancy", "id": "discrepancy", "type": "numeric"},
    ]
    # fmt: on

    metadata_table = dash_table.DataTable(
        data=metadata[metadata_columns].to_dict("records"),
        sort_action="native",
        filter_action="native",
        columns=table_columns,
        page_action="none",  # or page_size=5
        style_table={"height": "200px", "overflowY": "auto"},
        style_cell={"minWidth": 25, "maxWidth": 150, "width": "auto"},
        style_header={"fontWeight": "bold"},
        fixed_rows={"headers": True},
        row_selectable="single",
        selected_rows=[
            0,
        ],
        persisted_props=["selected_rows", "filter_query", "sort_by"],
        id="metadata_table",
    )

    buttons = dbc.ButtonGroup(
        [
            dbc.Button("Previous ImageID", id="previous", outline=True),
            dbc.Button("Next ImageID", id="next", outline=True),
        ],
        size="lg",
        style={"width": "100%"},
    )
    body = dbc.CardBody([metadata_table, buttons])

    return dbc.Card(id="metadata_card", children=[body])


def get_image_component() -> dcc.Graph:
    image_fig = px.imshow(
        np.zeros((128, 128, 3), dtype=np.uint8),
        binary_backend="jpg",
    )
    image_fig.update_layout(
        margin=dict(l=0, r=0, b=0, t=0, pad=4),
        dragmode="drawclosedpath",
    )

    image_graph = dcc.Graph(
        id="image_graph",
        figure=image_fig,
        config={
            "modeBarButtonsToAdd": ["drawclosedpath", "eraseshape"],
            "modeBarButtonsToRemove": [
                "resetScale2d",
                "hoverClosestCartesian",
                "hoverCompareCartesian",
                "toggleSpikelines",
            ],
        },
    )

    return image_graph


def get_annotation_component() -> dbc.Card:
    annotation_card = dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(html.H2("Metadata"), md=7),
                        dbc.Col(
                            dbc.Button(
                                "Save annotations",
                                id="save",
                                outline=True,
                            ),
                            md=4,
                        ),
                    ]
                )
            ),
            dbc.CardBody(
                [
                    dbc.Row(
                        dbc.Col(
                            [
                                html.H5("Blurry image ? "),
                                dcc.RadioItems(
                                    id="radio-blurry",
                                    options=[
                                        {"label": "   No", "value": 0},
                                        {"label": "   Blurry ?  ", "value": -1},
                                        {"label": "Yes    ", "value": 1},
                                    ],
                                    labelStyle={
                                        "display": "inline-block",
                                        "padding": "0px 12px 12px 0px",
                                    },
                                    value=-1,
                                ),
                                html.H5("Flash ? "),
                                dcc.RadioItems(
                                    id="radio-flash",
                                    options=[
                                        {"label": "   No", "value": 0},
                                        {"label": "   Flash ?  ", "value": -1},
                                        {"label": "Yes    ", "value": 1},
                                    ],
                                    labelStyle={
                                        "display": "inline-block",
                                        "padding": "0px 12px 12px 0px",
                                    },
                                    value=-1,
                                ),
                                html.H5("Relevant image ? "),
                                dcc.RadioItems(
                                    id="radio-relevant",
                                    options=[
                                        {"label": "Yes    ", "value": 1},
                                        {"label": "   Relevant ?  ", "value": -1},
                                        {"label": "   No", "value": 0},
                                    ],
                                    labelStyle={
                                        "display": "inline-block",
                                        "padding": "0px 12px 12px 0px",
                                    },
                                    value=-1,
                                ),
                                html.H5("Valid image ? "),
                                dcc.RadioItems(
                                    id="radio-valid",
                                    options=[
                                        {"label": "Yes    ", "value": 1},
                                        {"label": "   Valid ?  ", "value": -1},
                                        {"label": "   No", "value": 0},
                                    ],
                                    labelStyle={
                                        "display": "inline-block",
                                        "padding": "0px 12px 12px 0px",
                                    },
                                    value=-1,
                                ),
                                dbc.Input(
                                    id="input-text",
                                    type="text",
                                    placeholder="Plain text observations .. ",
                                ),
                                # add items here
                                html.H5("Internal data "),
                                html.Pre(
                                    id="display-internal-data",
                                    children=json.dumps(DEFAULT_TO_DISPLAY, indent=2),
                                ),
                                html.H5("Logs "),
                                html.Pre(id="display-logs", children=""),
                            ],
                        ),
                    )
                ]
            ),
        ],
    )
    return annotation_card


def get_data_store(start_data: dict) -> dcc.Store:
    # To keep ?
    return dcc.Store(
        id="all-data",
        data=start_data,
    )
