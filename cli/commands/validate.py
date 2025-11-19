import typer
from typing import Annotated
from cli.internal.utility.config import read_config
from cli.internal.aws.session import create_session

app = typer.Typer()

@app.command()
def validate(
    file_path: Annotated[str, typer.Option("-c", "--config", help="Config file used for defining resources")]
):
    config = read_config(file_path)
    provider = config["provider"]["name"]
    auth = config["auth"]
    session = create_session(auth)
    region = config["provider"]["region"]
