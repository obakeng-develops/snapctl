import yaml
from typing import Any


def read_config(file_path: str) -> dict[str, Any]:
    if file_path is None:
        raise ValueError("Config file path must be provided.")

    with open(file_path, "r") as file:
        config: dict[str, Any] = yaml.safe_load(file)
    return config
