import yaml


def read_config(file_path: str) -> dict:
    if file_path is None:
        raise ValueError("Config file path must be provided.")

    with open(file_path, "r") as file:
        config = yaml.safe_load(file)
    return config
