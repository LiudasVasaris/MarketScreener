"""Helper functions"""
import json
from pathlib import Path
from typing import Dict


def get_json_content(path: Path) -> Dict:
    """ Opens json file given path and returns contents of it
    :param path: Path to json file
    :return: contents of the file
    """
    with open(path, 'r') as file:
        json_variable = json.load(file)
    return json_variable
