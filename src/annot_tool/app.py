import json
import re

from datetime import datetime

import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
import numpy as np
import pandas as pd
import plotly.express as px

from dash import Dash, Input, Output, State, callback, callback_context
from loguru import logger
from skimage import io

from annot_tool.components import (
    get_annotation_component,
    get_data_store,
    get_image_component,
    get_metadata_component,
)
from annot_tool.data import DEFAULT_DATA_VALUES, save_data_to_json


def get_app(metadata: pd.DataFrame, start_data: dict, output_file: str) -> Dash:
    external_stylesheets = [
        dbc.themes.BOOTSTRAP,
    ]
    app = Dash(__name__, external_stylesheets=external_stylesheets)

    metadata_card = get_metadata_component(metadata)
    annotation_card = get_annotation_component()
    image_graph = get_image_component()
    data_store = get_data_store(start_data=start_data)

    # layout = html.Div([metadata_card])
    layout = html.Div(
        [
            dbc.Container(
                [
                    dbc.Row(
                        [
                            dbc.Col([metadata_card, image_graph], md=7),
                            dbc.Col(annotation_card, md=5),
                            data_store,
                        ],
                    ),
                ],
                fluid=True,
            ),
        ]
    )

    @callback(
        Output("metadata_table", "selected_rows"),
        [
            Input("previous", "n_clicks"),
            Input("next", "n_clicks"),
        ],
        [
            State("metadata_table", "derived_virtual_indices"),
            State("metadata_table", "derived_virtual_selected_rows"),
            State("metadata_table", "selected_rows"),
        ],
    )
    def previous_next_selected_row(
        previous_n_clicks,
        next_n_clicks,
        derived_virtual_indices,
        derived_virtual_selected_rows,
        selected_rows,
    ):
        logger.debug("callback previous_next() : ")
        logger.debug(f"previous_n_clicks : {previous_n_clicks} | {type(previous_n_clicks)}")
        logger.debug(f"next_n_clicks : {next_n_clicks} | {type(next_n_clicks)}")

        logger.debug(f"derived_virtual_indices : {derived_virtual_indices} | {type(derived_virtual_indices)}")
        logger.debug(
            f"derived_virtual_selected_rows : {derived_virtual_selected_rows} | {type(derived_virtual_selected_rows)}"
        )

        logger.debug(f"selected_rows : {selected_rows} | {type(selected_rows)}")

        cbcontext = [p["prop_id"] for p in callback_context.triggered][0]
        logger.debug(f"cbcontext : {cbcontext} | {type(cbcontext)}")

        if cbcontext not in ["previous.n_clicks", "next.n_clicks"]:
            return []

        current_selected_row = selected_rows[0]
        logger.debug(f"current_selected_row : {current_selected_row} | {type(current_selected_row)}")
        current_derived_virtual_selected_row_index = np.argwhere(
            np.asarray(derived_virtual_indices) == current_selected_row
        )[0][0]
        logger.debug(
            f"current_derived_virtual_selected_row_index : {current_derived_virtual_selected_row_index} | {type(current_derived_virtual_selected_row_index)}"
        )

        new_derived_virtual_selected_row_index = current_derived_virtual_selected_row_index

        # new_active_cell = active_cell.copy()
        if cbcontext == "previous.n_clicks":
            # new_active_cell["row"] = (active_cell["row"] - 1) % metadata.shape[0]
            new_derived_virtual_selected_row_index = (current_derived_virtual_selected_row_index - 1) % len(
                derived_virtual_indices
            )
        if cbcontext == "next.n_clicks":
            # new_active_cell["row"] = (active_cell["row"] + 1) % metadata.shape[0]
            new_derived_virtual_selected_row_index = (current_derived_virtual_selected_row_index + 1) % len(
                derived_virtual_indices
            )
        # new_active_cell["row_id"] = derived_virtual_row_ids[new_active_cell["row"]]
        # return (new_active_cell,)
        logger.debug(
            f"new_derived_virtual_selected_row_index :{new_derived_virtual_selected_row_index} | {type(new_derived_virtual_selected_row_index)}"
        )
        new_selected_row = derived_virtual_indices[new_derived_virtual_selected_row_index]
        logger.debug(f"new_selected_row : {new_selected_row} | {type(new_selected_row)}")

        return [
            new_selected_row,
        ]

    @callback(
        Output("image_graph", "figure"),
        Input("metadata_table", "derived_virtual_selected_row_ids"),
        State("all-data", "data"),
    )
    def update_image_figure(derived_virtual_selected_row_ids, all_data):
        logger.debug("callback update_image_figure() : ")
        logger.debug(f"derived_virtual_selected_row_ids : {derived_virtual_selected_row_ids}")

        if derived_virtual_selected_row_ids is None or len(derived_virtual_selected_row_ids) == 0:
            img = np.zeros((128, 128, 3), dtype=np.uint8)
            shapes = []

        else:
            image_id = derived_virtual_selected_row_ids[0]
            try:
                shapes = all_data[image_id]["shapes"]
                image_path = metadata.at[image_id, "image_path"]
                img = io.imread(image_path)
            except (Exception,) as e:
                logger.warning(f"Impossible to load image for ImageID={image_id}")
                logger.info(str(e))
                img = np.zeros((128, 128, 3), dtype=np.uint8)
                shapes = []

        new_fig = px.imshow(img, binary_backend="jpg")
        new_fig.update_layout(
            shapes=shapes,
            # reduce space between image and graph edges
            margin=dict(l=0, r=0, b=0, t=0, pad=4),
            dragmode="drawclosedpath",
        )
        return new_fig

    @callback(
        [
            Output("radio-blurry", "value"),
            Output("radio-flash", "value"),
            Output("radio-relevant", "value"),
            Output("radio-valid", "value"),
            Output("input-text", "value"),
        ],
        Input("metadata_table", "derived_virtual_selected_row_ids"),
        State("all-data", "data"),
    )
    def update_radio_items(derived_virtual_selected_row_ids, all_data):
        logger.debug("callback update_image_figure() : ")
        logger.debug(f"derived_virtual_selected_row_ids : {derived_virtual_selected_row_ids}")

        if derived_virtual_selected_row_ids is None or len(derived_virtual_selected_row_ids) == 0:
            return dash.no_update

        image_id = derived_virtual_selected_row_ids[0]
        data = all_data[image_id]

        return data["blurry"], data["flash"], data["relevant"], data["valid"], data["text"]

    @callback(
        Output("all-data", "data"),
        [
            Input("image_graph", "relayoutData"),
            Input("radio-blurry", "value"),
            Input("radio-flash", "value"),
            Input("radio-relevant", "value"),
            Input("radio-valid", "value"),
            Input("input-text", "value"),
        ],
        [State("metadata_table", "derived_virtual_selected_row_ids"), State("all-data", "data")],
    )
    def update_data_store(
        graph_relayout_data,
        blurry_value,
        flash_value,
        relevant_value,
        valid_value,
        text_value,
        derived_virtual_selected_row_ids,
        all_data,
    ):
        logger.debug("callback update_data_store() : ")
        logger.debug(f"graph_relayout_data : {graph_relayout_data} | {type(graph_relayout_data)}")
        logger.debug(f"blurry_value : {blurry_value} | {type(blurry_value)}")
        logger.debug(f"relevant_value : {relevant_value} | {type(relevant_value)}")
        logger.debug(f"valid_value : {valid_value} | {type(valid_value)}")
        logger.debug(f"flash_value : {flash_value} | {type(flash_value)}")
        logger.debug(f"text_value : {text_value} | {type(text_value)}")
        logger.debug(
            f"derived_virtual_selected_row_ids : {derived_virtual_selected_row_ids} | {type(derived_virtual_selected_row_ids)}"
        )
        logger.debug(f"all_data : {all_data} | {type(all_data)}")

        cbcontext = [p["prop_id"] for p in callback_context.triggered][0]
        logger.debug(f"cbcontext : {cbcontext} | {type(cbcontext)}")

        if derived_virtual_selected_row_ids is None or len(derived_virtual_selected_row_ids) == 0:
            logger.debug("No selected row")
            return dash.no_update
        image_id = derived_virtual_selected_row_ids[0]

        if cbcontext in [
            "radio-blurry.value",
            "radio-flash.value",
            "radio-relevant.value",
            "radio-valid.value",
            "input-text.value",
        ]:
            data = all_data[image_id]
            data["blurry"] = blurry_value
            data["flash"] = flash_value
            data["relevant"] = relevant_value
            data["valid"] = valid_value
            data["text"] = text_value
            all_data[image_id] = data
            return all_data

        if cbcontext == "image_graph.relayoutData":
            logger.debug("Try to add new annotation ... ")
            logger.debug("keys : ", list(graph_relayout_data.keys()))
            for k, v in graph_relayout_data.items():
                print(type(k), k)
                print(type(v), v)
            keys = list(graph_relayout_data.keys())
            if "shapes" in keys:
                shapes = graph_relayout_data["shapes"]
                all_data[image_id]["shapes"] = shapes

            elif re.match("shapes\[[0-9]+\].path", keys[0]):
                key = keys[0]
                ind = int(key.split("[")[-1].split("]")[0])
                logger.debug("Update shape : ", ind)
                path = graph_relayout_data[key]
                shapes = all_data[image_id]["shapes"]
                shapes[ind]["path"] = path
                all_data[image_id]["shapes"] = shapes

            return all_data
        else:
            return dash.no_update

    @app.callback(
        Output("display-internal-data", "children"),
        [Input("metadata_table", "derived_virtual_selected_row_ids"), Input("all-data", "data")],
    )
    def update_internal_data(derived_virtual_selected_row_ids, all_data):
        logger.debug("callback update_internal_data() : ")
        logger.debug(f"derived_virtual_selected_row_ids : {derived_virtual_selected_row_ids}")
        logger.debug(f"all_data : {all_data}")

        if derived_virtual_selected_row_ids is None or len(derived_virtual_selected_row_ids) == 0:
            return json.dumps(DEFAULT_DATA_VALUES, indent=2)

        image_id = derived_virtual_selected_row_ids[0]

        to_display = dict()
        to_display["data"] = all_data[image_id]
        to_display["data"]["shapes"] = [shape["path"] for shape in to_display["data"]["shapes"]]

        return json.dumps(to_display, indent=2)

    @app.callback(
        Output("display-logs", "children"),
        [Input("metadata_table", "derived_virtual_selected_row_ids"), Input("save", "n_clicks")],
        State("all-data", "data"),
    )
    def save_and_update_logs(derived_virtual_selected_row_ids, save_button_clicks, all_data):
        logger.debug("save_and_update_logs()")
        logger.debug(f"derived_virtual_selected_row_ids : {derived_virtual_selected_row_ids}")
        logger.debug(f"save_button_clicks : {save_button_clicks}")
        logger.debug(f"all_data : {all_data}")

        cbcontext = [p["prop_id"] for p in callback_context.triggered][0]

        save_data_to_json(all_data, output_file=output_file)

        if derived_virtual_selected_row_ids is None or len(derived_virtual_selected_row_ids) == 0:
            return "No selected row"

        if cbcontext == "save.n_clicks":
            return f"{datetime.now()} manual save. Selected ImageID={derived_virtual_selected_row_ids[0]}"
        else:
            return f"{datetime.now()} automatic save. Selected ImageID={derived_virtual_selected_row_ids[0]}"

    app.layout = layout
    return app
