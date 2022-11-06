import json
import os

import pandas as pd

from annot_tool import DATA_DIR


DEFAULT_SHAPE_DICT = {
    "editable": True,
    "xref": "x",
    "yref": "y",
    "layer": "above",
    "opacity": 1,
    "line": {"color": "#444", "width": 4, "dash": "solid"},
    "fillcolor": "rgba(0,0,0,0)",
    "fillrule": "evenodd",
    "type": "path",
    "path": "",
}

DEFAULT_DATA_VALUES = {
    "blurry": -1,
    "flash": -1,
    "relevant": -1,
    "valid": -1,
    "text": None,
    "shapes": [],
}


def load_metadata() -> pd.DataFrame:
    metadata = pd.read_csv(os.path.join(DATA_DIR, "metadata.csv"))

    # update 'image_path', to get full path
    metadata["image_path"] = metadata["image_path"].apply(
        lambda image_path: os.path.join(DATA_DIR, image_path)
    )

    metadata = metadata.astype(
        dtype={
            "image_id": "str",
            "label": "int",
            "source": "str",
            "image_path": "str",
            "discrepancy": "float",
        }
    )
    # set 'image_id' as index (but keep the column 'image_id' unchanged
    metadata.set_index("image_id", inplace=True, drop=False)
    metadata.index.name = ""
    return metadata


def load_existing_json(output_file: str) -> dict:
    with open(output_file, "r") as f:
        saved_data: dict = json.load(f)

    start_data = {}

    for image_id, data in saved_data.items():
        data["text"] = None if data["text"] == "" else data["text"]
        data["shapes"] = []
        shapes = data.pop("shapes")
        for shape in shapes:
            shape_dict = DEFAULT_SHAPE_DICT.copy()
            shape_dict["path"] = shape
            data["shapes"].append(shape_dict)
        start_data[image_id] = data

    return start_data


def save_data_to_json(all_data: dict, output_file: str) -> None:
    to_save = dict()

    for image_id, data in all_data.items():
        to_save[image_id] = {
            "blurry": data["blurry"],
            "flash": data["flash"],
            "relevant": data["relevant"],
            "valid": data["valid"],
            "text": data["text"] if data["text"] is not None else "",
            "shapes": [shape["path"] for shape in data["shapes"]],  # dumpy only 'path' in shape dict.
        }

    with open(output_file, "w") as f:
        json.dump(to_save, f, indent=2)
