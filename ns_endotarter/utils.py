import os
import shutil
import gzip

import toml
import requests

from ns_endotarter import info


def load_config(file_path):
    with open(file_path) as f:
        return toml.load(f)


def canonical(name):
    """Convert name to lower case and replace underscore
    with space.

    Args:
        name (str): Name

    Returns:
        str: Canonicalized name
    """

    return name.lower().replace(' ', '_')


def load_dump(file_path):
    """Load data dump file

    Args:
        file_path (str): Dump file path

    Returns:
        file: File object
    """

    if not os.path.exists(file_path):
        resp = requests.get(info.DATA_DUMP_URL, stream=True)

        with open(file_path, 'w') as f:
            shutil.copyfileobj(resp.raw, f)

    dump = gzip.open(file_path)
    return dump