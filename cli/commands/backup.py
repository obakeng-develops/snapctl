import typer
import boto3
import time
from typing import Annotated, Dict, Any
from datetime import datetime

from cli.internal.utility.config import read_config
from cli.internal.aws.session import create_session
from cli.internal.aws.client import get_client
from cli.internal.aws.resource_filtering import list_resource_by_tag

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

def initiate_snapshot(resource: dict[str, any], session: boto3.Session, region: None = "us-east-1") -> str:
    snapshot_results = []
    resource_id = resource['DBClusterIdentifier']
    prefix = "backup"
                        
    try:
        snapshot_result = create_cluster_snapshot(resource_id, prefix, session, region)
        snapshot_results.append({
            "cluster_id": resource_id,
            "snapshot_id": snapshot_result["DBClusterSnapshotIdentifier"],
            "status": "initiated",
            "snapshot_arn": snapshot_result["DBClusterSnapshotArn"]
        })
                            
        typer.echo(f"Successfully initiated snapshot for cluster: {resource_id}")
    except Exception as e:
        snapshot_results.append({
            'cluster_id': resource_id,
            'status': 'failed',
            'error': str(e)
        })
        typer.echo(f"Failed to create snapshot for cluster {resource_id}: {str(e)}")

def check_snapshot_status(snapshot_id: str, session: boto3.Session, region: str) -> str:
    """Check the current status of a snapshot."""
    client = get_client("rds", session, region)
    response = client.describe_db_cluster_snapshots(
        DBClusterSnapshotIdentifier=snapshot_id
    )
    return response['DBClusterSnapshots'][0]['Status']

def create_cluster_snapshot(cluster_id: str, prefix: str, session: boto3.Session, region: str) -> Dict[str, Any]:
    timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    snapshot_id = f"{prefix}-{cluster_id}-{timestamp}"
    
    try:
        client = get_client("rds", session, region)
        
        response = client.create_db_cluster_snapshot(
            DBClusterSnapshotIdentifier=snapshot_id,
            DBClusterIdentifier=cluster_id,
            Tags=[
                {
                    "Key": "resource",
                    "Value": f"{cluster_id}"
                },
                {
                    "Key": "createdAt",
                    "Value": timestamp
                },
                {
                    "Key": "prefix",
                    "Value": prefix
                },
                {
                    "Key": "version",
                    "Value": "0.1.0"
                },
                {
                    "Key": "origin",
                    "Value": "snapctl"
                }
            ]
        )
        
        return response['DBClusterSnapshot']
        
    except Exception as e:
        typer.echo(f"Error creating snapshot for {cluster_id}: {str(e)}")
        raise
