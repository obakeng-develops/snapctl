import typer
import structlog
from typing import Annotated
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound
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
    ] = False,
):
    """Validate configuration file and optionally test AWS authentication."""
    try:
        config = read_config(file_path)
    except FileNotFoundError:
        logger.error(f"Config file not found: {file_path}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Failed to read config: {e}")
        raise typer.Exit(code=1)
    
    # Validate required top-level keys
    app_name = config.get("app", None)
    provider = config.get("provider", None)
    backup = config.get("backup", None)

    if app_name is None:
        logger.error("App name key is required")
        raise typer.Exit(code=1)

    if provider is None:
        logger.error("Provider key is required")
        raise typer.Exit(code=1)

    if provider.get("name") is None:
        logger.error("Provider name key is required")
        raise typer.Exit(code=1)

    if provider.get("region", None) is None:
        logger.error("Region key is required")
        raise typer.Exit(code=1)

    if backup is None:
        logger.error("Backup configuration is required")
        raise typer.Exit(code=1)

    if backup.get("resources", None) is None:
        logger.error("Backup resources key is required")
        raise typer.Exit(code=1)

    resources = backup.get("resources", [])

    if not resources:
        logger.error("At least one resource is required")
        raise typer.Exit(code=1)

    # Validate each resource
    for idx, resource in enumerate(resources):
        if not resource.get("type"):
            logger.error(f"Resource {idx}: type is required")
            raise typer.Exit(code=1)

        if not resource.get("name"):
            logger.error(f"Resource {idx}: name is required")
            raise typer.Exit(code=1)

        if not resource.get("discover"):
            logger.error(f"Resource {idx}: discover is required")
            raise typer.Exit(code=1)

    logger.info("✓ Configuration structure is valid")

    # Optionally validate authentication
    if auth:
        if provider["name"] == "aws":
            validate_auth(config)
        else:
            logger.error(f"Provider {provider['name']} is not supported yet")
            raise typer.Exit(code=1)
    else:
        logger.info("ℹ Use --auth flag to validate AWS credentials")

    typer.echo("✅ Validation successful!")


def validate_auth(config: dict):
    """Validate AWS authentication by attempting to get caller identity."""
    auth = config.get("auth")
    
    if not auth:
        logger.error("Auth configuration is required")
        raise typer.Exit(code=1)

    if "profile" in auth:
        validate_profile(auth)
    elif "role_arn" in auth:
        validate_role_arn(auth)
    else:
        logger.error("No valid authentication method found (profile or role_arn)")
        raise typer.Exit(code=1)


def validate_profile(auth: dict):
    """Validate AWS profile by testing STS access."""
    profile = auth["profile"]
    
    try:
        session = create_session(auth)
        client = session.client("sts")
        response = client.get_caller_identity()
        
        logger.info(f"✓ Profile '{profile}' is valid")
        logger.info(f"  Account: {response['Account']}")
        logger.info(f"  ARN: {response['Arn']}")
    except ProfileNotFound:
        logger.error(f"AWS profile '{profile}' not found in ~/.aws/credentials")
        raise typer.Exit(code=1)
    except NoCredentialsError:
        logger.error("No AWS credentials found. Configure with 'aws configure'")
        raise typer.Exit(code=1)
    except ClientError as e:
        logger.error(f"AWS API error: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Unexpected error validating profile: {e}")
        raise typer.Exit(code=1)


def validate_role_arn(auth: dict):
    """Validate AWS role by attempting to assume it."""
    role_arn = auth["role_arn"]
    
    try:
        session = create_session(auth)
        client = session.client("sts")
        response = client.get_caller_identity()
        
        logger.info(f"✓ Role ARN '{role_arn}' is valid")
        logger.info(f"  Account: {response['Account']}")
        logger.info(f"  ARN: {response['Arn']}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'AccessDenied':
            logger.error(f"Access denied when assuming role: {role_arn}")
        else:
            logger.error(f"Failed to assume role: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Unexpected error validating role: {e}")
        raise typer.Exit(code=1)
