import resource
import typer
import boto3
import time
from typing import Annotated, Dict, Any
from datetime import datetime

from cli.internal.utility.config import read_config
from cli.internal.aws.session import create_session
from cli.internal.aws.client import get_client
from cli.internal.aws.resource_filtering import list_resource_by_tag
from cli.internal.aws.backup import backup_rds_resources

POLL_INTERVAL = 30 #seconds

app = typer.Typer()

@app.command()
def backup(
    file_path: Annotated[str, typer.Option("-c", "--config", help="Config file used for defining resources")],
    parallel: Annotated[int, typer.Option("-p", "--parallel", help="Number of backups to run in parallel")] = 3
):
    config = read_config(file_path)
    provider = config["provider"]["name"]
    
    auth = config["auth"]
    session = create_session(auth)
    region = config["provider"]["region"]
    
    match provider:
        case "aws":
            for resource_config in config["protect"]["resources"]:
                service_type = resource_config["type"]
                resource_name = resource_config["name"]
                tags = resource_config["tags"]
                
                typer.echo(f"\n=== Processing {resource_name} ({service_type}) ===")
                typer.echo(f"Discovering resources with: {tags}")
                
                client = get_client(service_type, session, region)
                resources = list_resource_by_tag(client, service_type, tags)
                
                if not resources:
                    typer.echo(f"No resources found for {resource_name}")
                
                typer.echo(f"Found {len(resources)} resources(s)")
                        
                match service_type:
                    case "rds":    
                        backup_rds_resources(resources, session, region, parallel)
                    case _:
                        typer.echo(f"Resource type {service_type} is not supported yet.")
                        raise typer.Exit(code=1)
        case _:
            typer.echo(f"Provider {provider} is not supported yet.")
            raise typer.Exit(code=1)
