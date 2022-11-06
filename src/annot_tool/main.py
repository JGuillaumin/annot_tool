import argparse
import os
import random
import string

from _datetime import datetime
from loguru import logger

from annot_tool.app import get_app
from annot_tool.constants import DEBUG, HOST, PORT
from annot_tool.data import DEFAULT_DATA_VALUES, load_existing_json, load_metadata


def main() -> None:
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument(
        "-f",
        "--file",
        dest="output_file",
        default="{}_{}.json".format(
            datetime.now().strftime("%d-%m-%Y_%H-%M-%S"),
            "".join(random.choices(string.ascii_uppercase + string.digits, k=6)),
        ),
        type=str,
    )
    params = argument_parser.parse_args()
    logger.info(f"params : {params}")

    metadata = load_metadata()
    if os.path.isfile(params.output_file):
        start_data = load_existing_json(params.output_file)
    else:
        start_data = {image_id: DEFAULT_DATA_VALUES for image_id in metadata["image_id"].values}

    app = get_app(metadata=metadata, start_data=start_data, output_file=params.output_file)
    app.server.run(host=HOST, port=PORT, debug=DEBUG)


if __name__ == "__main__":
    main()
