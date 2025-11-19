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
    
    match provider:
        case "aws":
            service = config["protect"]["resources"][0]["type"]
            region = config["provider"]["region"]
            tags = config["protect"]["resources"][0]["discover"]
            resource_type = ""
            
            client = get_client(service, session, region)
            
            resources = list_resource_by_tag(client, service, tags)
            
            available_clusters = [
                resource for resource in resources if resource["Status"] == "available"
            ]
            
            resource_type = ""
            if available_clusters and available_clusters[0]["Engine"].startswith("aurora"):
                resource_type = "rds"
                    
            match resource_type:
                case "rds":    
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
                                
                case _:
                    typer.echo(f"Resource type {resource_type} is not supported yet.")
                    raise typer.Exit(code=1)
        case _:
            typer.echo(f"Provider {provider} is not supported yet.")
            raise typer.Exit(code=1)
