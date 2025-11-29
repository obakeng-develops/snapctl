from typing import Dict, Any
import structlog
import boto3
from datetime import datetime
from .client import get_client

logger = structlog.get_logger()


def initiate_snapshot(
    resource: dict[str, Any], session: boto3.Session, region: str = "us-east-1"
) -> Dict[str, Any]:
    snapshot_results = []
    resource_id = resource["DBClusterIdentifier"]
    prefix = "backup"

    try:
        snapshot_result = create_cluster_snapshot(resource_id, prefix, session, region)
        snapshot_results.append(
            {
                "cluster_id": resource_id,
                "snapshot_id": snapshot_result["DBClusterSnapshotIdentifier"],
                "status": "initiated",
                "snapshot_arn": snapshot_result["DBClusterSnapshotArn"],
            }
        )

        logger.info(f"Successfully initiated snapshot for cluster: {resource_id}")
        return snapshot_result
    except Exception as e:
        snapshot_results.append(
            {"cluster_id": resource_id, "status": "failed", "error": str(e)}
        )
        logger.error(f"Failed to create snapshot for cluster {resource_id}: {str(e)}")
        raise


def check_snapshot_status(snapshot_id: str, session: boto3.Session, region: str) -> str:
    """Check the current status of a snapshot."""
    client = get_client("rds", session, region)
    response = client.describe_db_cluster_snapshots(
        DBClusterSnapshotIdentifier=snapshot_id
    )
    status: str = response['DBClusterSnapshots'][0]['Status']
    return status


def create_cluster_snapshot(
    cluster_id: str, prefix: str, session: boto3.Session, region: str
) -> Dict[str, Any]:
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    snapshot_id = f"{prefix}-{cluster_id}-{timestamp}"

    try:
        client = get_client("rds", session, region)

        response = client.create_db_cluster_snapshot(
            DBClusterSnapshotIdentifier=snapshot_id,
            DBClusterIdentifier=cluster_id,
            Tags=[
                {"Key": "resource", "Value": f"{cluster_id}"},
                {"Key": "createdAt", "Value": timestamp},
                {"Key": "prefix", "Value": prefix},
                {"Key": "version", "Value": "0.1.0"},
                {"Key": "origin", "Value": "snapctl"},
            ],
        )

        result: Dict[str, Any] = response['DBClusterSnapshot']
        return result
    except Exception as e:
        logger.error(f"Error creating snapshot for {cluster_id}: {str(e)}")
        raise
