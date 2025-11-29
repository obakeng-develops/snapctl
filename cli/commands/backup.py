import typer
import structlog
from typing import Annotated

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
    config = read_config(file_path)
    provider = config["provider"]["name"]

    auth = config["auth"]
    session = create_session(auth)
    region = config["provider"]["region"]

    match provider:
        case "aws":
            for resource_config in config["backup"]["resources"]:
                service_type = resource_config["type"]
                resource_name = resource_config["name"]
                tags = resource_config["tags"]

                logger.info(f"\n=== Processing {resource_name} ({service_type}) ===")
                logger.info(f"Discovering resources with: {tags}")

                client = get_client(service_type, session, region)
                resources = list_resource_by_tag(client, service_type, tags)

                if not resources:
                    logger.error(f"No resources found for {resource_name}")

                logger.info(f"Found {len(resources)} resources(s)")

                match service_type:
                    case "rds":
                        backup_rds_resources(resources, session, region, parallel)
                    case _:
                        logger.error(
                            f"Resource type {service_type} is not supported yet."
                        )
                        raise typer.Exit(code=1)
        case _:
            logger.error(f"Provider {provider} is not supported yet.")
            raise typer.Exit(code=1)
