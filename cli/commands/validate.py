import typer
import structlog
from typing import Annotated
from cli.internal.utility.config import read_config
from cli.internal.aws.session import create_session

app = typer.Typer()

logger = structlog.get_logger()


@app.command()
def validate(
    file_path: Annotated[
        str,
        typer.Option("-c", "--config", help="Config file used for defining resources"),
    ],
    auth: Annotated[
        bool, typer.Option("-a", "--auth", help="Validate authentication")
    ] = None,
):
    config = read_config(file_path)
    app_name = config.get("app", None)
    provider = config.get("provider", None)
    backup = config.get("backup", None)

    if app_name is None:
        logger.error("App name key is required")
        raise typer.Exit(code=1)

    if provider is None:
        logger.error("Provider key is required")
        raise typer.Exit(code=1)

    if provider["name"] is None:
        logger.error("Provider name key is required")
        raise typer.Exit(code=1)

    if provider.get("region", None) is None:
        logger.error("Region key is required")
        raise typer.Exit(code=1)

    if backup.get("resources", None) is None:
        logger.error("Protect resources key is required")
        raise typer.Exit(code=1)

    resources = backup.get("resources", None)

    if resources is None:
        logger.error("Resources key is required")
        raise typer.Exit(code=1)

    for resource in resources:
        if resource["type"] is None:
            logger.error("Resource type is required")
            raise typer.Exit(code=1)

        if resource["name"] is None:
            logger.error("Resource name is required")
            raise typer.Exit(code=1)

        if resource["discover"] is None:
            logger.error("Resource discover is required")
            raise typer.Exit(code=1)

    if auth:
        if provider["name"] == "aws":
            validate_auth(config)
        else:
            logger.error("Provider is not supported yet")
            raise typer.Exit(code=1)
    else:
        logger.error("Auth is required")
        raise typer.Exit(code=1)

    logger.info("Validation successful")


def validate_auth(config: dict):
    auth = config["auth"]

    if "profile" in auth:
        validate_profile(auth)
    elif "role_arn" in auth:
        validate_role_arn(auth)
    else:
        logger.error("No valid authentication method found in config")
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
