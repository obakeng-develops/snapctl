import typer
import boto3
import time
from .snapshotting import initiate_snapshot, check_snapshot_status

POLL_INTERVAL = 30 #seconds

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
