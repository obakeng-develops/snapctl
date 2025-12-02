import typer
import structlog
from typing import Annotated
from botocore.exceptions import ClientError, NoCredentialsError

from cli.internal.utility.config import read_config
from cli.internal.aws.session import create_session
from cli.internal.aws.client import get_client
from cli.internal.aws.resource_filtering import list_resource_by_tag
from cli.internal.aws.backup import backup_rds_resources

POLL_INTERVAL = 30  # seconds

app = typer.Typer()

logger = structlog.get_logger()


@app.command()
def backup(
    file_path: Annotated[
        str,
        typer.Option("-c", "--config", help="Config file used for defining resources"),
    ],
    parallel: Annotated[
        int,
        typer.Option("-p", "--parallel", help="Number of backups to run in parallel"),
    ] = 3,
):
    """Execute backup for all configured resources."""
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
    region = config["provider"]["region"]

    # Create AWS session
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
                for resource_config in config["backup"]["resources"]:
                    service_type = resource_config["type"]
                    resource_name = resource_config["name"]
                    tags = resource_config["discover"]

                    logger.info(
                        f"\n=== Processing {resource_name} ({service_type}) ==="
                    )
                    logger.info(f"Discovering resources with: {tags}")

                    try:
                        client = get_client(service_type, session, region)
                        resources = list_resource_by_tag(client, service_type, tags)
                    except ClientError as e:
                        logger.error(f"AWS API error discovering resources: {e}")
                        continue
                    except Exception as e:
                        logger.error(f"Failed to discover resources: {e}")
                        continue

                    if not resources:
                        logger.error(f"No resources found for {resource_name}")
                        continue

                    logger.info(f"Found {len(resources)} resource(s)")

                    match service_type:
                        case "rds":
                            try:
                                backup_rds_resources(
                                    resources, session, region, parallel
                                )
                            except ClientError as e:
                                logger.error(f"AWS API error during backup: {e}")
                                logger.error(
                                    "Check IAM permissions for RDS snapshot creation"
                                )
                            except Exception as e:
                                logger.error(f"Backup failed: {e}")
                        case _:
                            logger.error(
                                f"Resource type {service_type} is not supported yet."
                            )
                            continue

            except KeyError as e:
                logger.error(f"Missing required configuration key: {e}")
                raise typer.Exit(code=1)
            except Exception as e:
                logger.error(f"Unexpected error during backup: {e}")
                raise typer.Exit(code=1)

        case _:
            logger.error(f"Provider {provider} is not supported yet.")
            raise typer.Exit(code=1)
