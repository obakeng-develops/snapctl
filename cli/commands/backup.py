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
from cli.internal.aws.snapshotting import initiate_snapshot, check_snapshot_status

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

def backup_rds_resources(resources: list[dict[str, any]], session: boto3.Session, region: str, parallel: int):
    """Backup RDS resources with parallel execution and polling."""
    available_clusters = [
        resource for resource in resources if resource["Status"] == "available"
    ]
    
    if not available_clusters:
        typer.echo("No available Aurora clusters found to backup")
        return

    typer.echo(f"Starting backup for {len(available_clusters)} Aurora cluster(s)")
    
    in_progress = []
    pending = list(available_clusters)

    while pending or in_progress:
        while len(in_progress) < parallel and pending:
            resource = pending.pop(0)
            snapshot_result = initiate_snapshot(resource, session, region)
            in_progress.append({
                                'cluster': resource['DBClusterIdentifier'],
                                'snapshot_id': snapshot_result['DBClusterSnapshotIdentifier'],
                                'snapshot_arn': snapshot_result['DBClusterSnapshotArn'],
                                'started': time.time()
            })
            typer.echo(f"Started backup: {snapshot_result['DBClusterSnapshotIdentifier']}")
                            
                        # Poll for completion
            if in_progress:
                time.sleep(POLL_INTERVAL)
                            
                completed = []
                for backup in in_progress:
                    status = check_snapshot_status(backup['snapshot_id'], session, region)
                    if status in ["available", "failed"]:
                        duration = time.time() - backup['started']
                        typer.echo(f"Backup {backup['snapshot_id']}: {status} (took {duration:.0f}s)")
                        completed.append(backup)
                                    
                    for backup in completed:
                        in_progress.remove(backup)
