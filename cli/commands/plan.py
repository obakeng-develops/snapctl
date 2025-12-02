import typer
from typing_extensions import Annotated
from botocore.exceptions import ClientError, NoCredentialsError

from cli.internal.utility.config import read_config
from cli.internal.aws.plan import aws_plan
from cli.internal.aws.session import create_session
import structlog

app = typer.Typer()
logger = structlog.get_logger()


@app.command()
def plan(
    file_path: Annotated[
        str,
        typer.Option("-c", "--config", help="Config file used for defining resources"),
    ],
):
    """Speculatively show a plan of all the resources that will be backed up."""
    try:
        config = read_config(file_path)
    except FileNotFoundError:
        logger.error(f"Config file not found: {file_path}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Failed to read config: {e}")
        raise typer.Exit(code=1)

    provider = config["provider"]["name"]
    auth = config["auth"]

    try:
        session = create_session(auth)
    except NoCredentialsError:
        logger.error(
            "No AWS credentials found. Configure with 'aws configure' or check your profile"
        )
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Failed to create AWS session: {e}")
        raise typer.Exit(code=1)

    match provider:
        case "aws":
            try:
                aws_plan(config, session)
            except ClientError as e:
                logger.error(f"AWS API error: {e}")
                logger.error("Check your IAM permissions for RDS describe operations")
                raise typer.Exit(code=1)
            except KeyError as e:
                logger.error(f"Missing required configuration key: {e}")
                raise typer.Exit(code=1)
            except Exception as e:
                logger.error(f"Unexpected error during plan: {e}")
                raise typer.Exit(code=1)
        case _:
            logger.error(f"Provider {provider} is not supported yet.")
            raise typer.Exit(code=1)
