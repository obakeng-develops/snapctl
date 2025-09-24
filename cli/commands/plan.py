import typer
from typing_extensions import Annotated

app = typer.Typer()

@app.command()
def plan(
    file_path: Annotated[str, typer.Option("-f", "--file", help="Config file used for defining resources")]
):
    """Speculatively show a plan of all the resources that will be backed up.
    """
    print("Hello from snapctl!")
