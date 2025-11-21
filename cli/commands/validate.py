import typer
from typing import Annotated
from cli.internal.utility.config import read_config
from cli.internal.aws.session import create_session

app = typer.Typer()

@app.command()
def validate(
    file_path: Annotated[str, typer.Option("-c", "--config", help="Config file used for defining resources")],
    auth: Annotated[bool, typer.Option("-a", "--auth", help="Validate authentication")] = None
):
    config = read_config(file_path)
    app_name = config.get("app", None)
    provider = config.get("provider", None)
    backup = config.get("backup", None)
    
    if app_name is None:
        typer.echo("App name key is required")
        raise typer.Exit(code=1)
    
    if provider is None:
        typer.echo("Provider key is required")
        raise typer.Exit(code=1)
    
    if provider["name"] is None:
        typer.echo("Provider name key is required")
        raise typer.Exit(code=1)
    
    if provider.get("region", None) is None:
        typer.echo("Region key is required")
        raise typer.Exit(code=1)
    
    if backup.get("resources", None) is None:
        typer.echo("Protect resources key is required")
        raise typer.Exit(code=1)
    
    resources = backup.get("resources", None)
    
    if resources is None:
        typer.echo("Resources key is required")
        raise typer.Exit(code=1)
    
    for resource in backup["resources"]:
        if resource["type"] is None:
            typer.echo("Resource type is required")
            raise typer.Exit(code=1)
        
        if resource["name"] is None:
            typer.echo("Resource name is required")
            raise typer.Exit(code=1)
        
        if resource["discover"] is None:
            typer.echo("Resource discover is required")
            raise typer.Exit(code=1)
    
    if auth:
        if provider["name"] == "aws":
            validate_auth(config)
        else:
            typer.echo("Provider is not supported yet")
            raise typer.Exit(code=1)
    else:
        typer.echo("Auth is required")
        raise typer.Exit(code=1)
        
    typer.echo("Validation successful")
    
def validate_auth(config: dict):
    auth = config["auth"]
    
    if "profile" in auth:
        validate_profile(auth)
    elif "role_arn" in auth:
        validate_role_arn(auth)
    else:
        typer.echo("No valid authentication method found in config")
        raise typer.Exit(code=1)
        
def validate_profile(auth: dict):
    profile = auth["profile"]
    session = create_session(auth)
    client = session.client("sts")
    client.get_caller_identity()
    typer.echo(f"Profile {profile} is valid")
    
def validate_role_arn(auth: dict):
    role_arn = auth["role_arn"]
    session = create_session(auth)
    client = session.client("sts")
    client.get_caller_identity()
    typer.echo(f"Role ARN {role_arn} is valid")
