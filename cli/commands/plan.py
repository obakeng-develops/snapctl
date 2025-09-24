import typer
from typing_extensions import Annotated

from cli.internal.config import read_config

app = typer.Typer()

@app.command()
def plan(
    file_path: Annotated[str, typer.Option("-f", "--file", help="Config file used for defining resources")]
):
    """Speculatively show a plan of all the resources that will be backed up.
    """
    config = read_config(file_path)
    
    print(config)
