import typer
from typing_extensions import Annotated

from cli.internal.utility.config import read_config
from cli.internal.aws.plan import aws_plan
from cli.internal.aws.session import create_session_with_profile, create_session_with_role

app = typer.Typer()

@app.command()
def plan(
    file_path: Annotated[str, typer.Option("-c", "--config", help="Config file used for defining resources")]
):
    """Speculatively show a plan of all the resources that will be backed up.
    """
    config = read_config(file_path)
    provider = config["provider"]["name"]
    
    auth = config["auth"]
    session = None
    if "role_arn" in auth:
        session = create_session_with_role(auth)
    elif "profile" in auth:
        session = create_session_with_profile(auth)
    else:
        raise ValueError("No valid authentication method found in config")
    
    match provider:
        case "aws":
            aws_plan(config, session)
        case _:
            typer.echo(f"Provider {provider} is not supported yet.")
            raise typer.Exit(code=1)
