import typer
from typing_extensions import Annotated

from cli.internal.config import read_config
from cli.internal.aws.plan import aws_plan

app = typer.Typer()

@app.command()
def plan(
    file_path: Annotated[str, typer.Option("-f", "--file", help="Config file used for defining resources")]
):
    """Speculatively show a plan of all the resources that will be backed up.
    """
    config = read_config(file_path)
    
    provider = config["provider"]["name"]
    
    match provider:
        case "aws":
            aws_plan(config)
        case _:
            typer.echo(f"Provider {provider} is not supported yet.")
            raise typer.Exit(code=1)
