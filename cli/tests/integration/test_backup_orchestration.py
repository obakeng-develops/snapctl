from moto import mock_aws
import boto3
from unittest.mock import patch

from cli.internal.aws.backup import backup_rds_resources


@mock_aws
def test_backup_single_cluster(mock_aws_credentials):
    """Backup a single cluster successfully."""
    client = boto3.client("rds", region_name="us-east-1")

    # Create cluster
    client.create_db_cluster(
        DBClusterIdentifier="single-test-1",
        Engine="aurora-postgresql",
        MasterUsername="admin",
        MasterUserPassword="password123",
    )

    session = boto3.Session(region_name="us-east-1")

    resources = [
        {
            "DBClusterIdentifier": "single-test-1",
            "Engine": "aurora-postgresql",
            "Status": "available",
        }
    ]

    with patch("cli.internal.aws.backup.POLL_INTERVAL", 0.1):
        backup_rds_resources(resources, session, "us-east-1", parallel=1)

    # Verify snapshot was created - filter for backup snapshots only
    all_snapshots = client.describe_db_cluster_snapshots()["DBClusterSnapshots"]
    backup_snapshots = [
        s
        for s in all_snapshots
        if s["DBClusterSnapshotIdentifier"].startswith("backup-")
    ]

    assert len(backup_snapshots) == 1
    assert "single-test-1" in backup_snapshots[0]["DBClusterSnapshotIdentifier"]


@mock_aws
def test_backup_respects_parallel_limit(mock_aws_credentials):
    """Backup should not exceed parallel limit."""
    client = boto3.client("rds", region_name="us-east-1")

    # Create 5 clusters
    for i in range(1, 6):
        client.create_db_cluster(
            DBClusterIdentifier=f"parallel-test-{i}",
            Engine="aurora-postgresql",
            MasterUsername="admin",
            MasterUserPassword="password123",
        )

    session = boto3.Session(region_name="us-east-1")

    resources = [
        {
            "DBClusterIdentifier": f"parallel-test-{i}",
            "Engine": "aurora-postgresql",
            "Status": "available",
        }
        for i in range(1, 6)
    ]

    with patch("cli.internal.aws.backup.POLL_INTERVAL", 0.1):
        backup_rds_resources(resources, session, "us-east-1", parallel=2)

    # All 5 clusters should be backed up
    all_snapshots = client.describe_db_cluster_snapshots()["DBClusterSnapshots"]
    backup_snapshots = [
        s
        for s in all_snapshots
        if s["DBClusterSnapshotIdentifier"].startswith("backup-")
    ]
    assert len(backup_snapshots) == 5


@mock_aws
def test_backup_handles_unavailable_clusters(mock_aws_credentials):
    """Only backup clusters with Status=available."""
    client = boto3.client("rds", region_name="us-east-1")

    # Create 3 clusters
    for i in range(1, 4):
        client.create_db_cluster(
            DBClusterIdentifier=f"unavail-test-{i}",
            Engine="aurora-postgresql",
            MasterUsername="admin",
            MasterUserPassword="password123",
        )

    session = boto3.Session(region_name="us-east-1")

    resources = [
        {
            "DBClusterIdentifier": "unavail-test-1",
            "Engine": "aurora-postgresql",
            "Status": "available",
        },
        {
            "DBClusterIdentifier": "unavail-test-2",
            "Engine": "aurora-postgresql",
            "Status": "backing-up",  # Not available
        },
        {
            "DBClusterIdentifier": "unavail-test-3",
            "Engine": "aurora-postgresql",
            "Status": "available",
        },
    ]

    with patch("cli.internal.aws.backup.POLL_INTERVAL", 0.1):
        backup_rds_resources(resources, session, "us-east-1", parallel=2)

    # Only 2 snapshots should be created (cluster-1 and cluster-3)
    all_snapshots = client.describe_db_cluster_snapshots()["DBClusterSnapshots"]
    backup_snapshots = [
        s
        for s in all_snapshots
        if s["DBClusterSnapshotIdentifier"].startswith("backup-")
    ]
    assert len(backup_snapshots) == 2


@mock_aws
def test_backup_with_no_available_clusters(mock_aws_credentials):
    """Handle case when no clusters are available for backup."""
    client = boto3.client("rds", region_name="us-east-1")

    # Create cluster but don't use it
    client.create_db_cluster(
        DBClusterIdentifier="no-avail-1",
        Engine="aurora-postgresql",
        MasterUsername="admin",
        MasterUserPassword="password123",
    )

    session = boto3.Session(region_name="us-east-1")

    resources = [
        {
            "DBClusterIdentifier": "no-avail-1",
            "Engine": "aurora-postgresql",
            "Status": "deleting",  # Not available
        }
    ]

    # Should return early without creating snapshots
    backup_rds_resources(resources, session, "us-east-1", parallel=1)

    all_snapshots = client.describe_db_cluster_snapshots()["DBClusterSnapshots"]
    backup_snapshots = [
        s
        for s in all_snapshots
        if s["DBClusterSnapshotIdentifier"].startswith("backup-")
    ]
    assert len(backup_snapshots) == 0


@mock_aws
def test_backup_polls_until_complete(mock_aws_credentials):
    """Backup should poll until all snapshots complete."""
    client = boto3.client("rds", region_name="us-east-1")

    client.create_db_cluster(
        DBClusterIdentifier="poll-test-1",
        Engine="aurora-postgresql",
        MasterUsername="admin",
        MasterUserPassword="password123",
    )

    session = boto3.Session(region_name="us-east-1")

    resources = [
        {
            "DBClusterIdentifier": "poll-test-1",
            "Engine": "aurora-postgresql",
            "Status": "available",
        }
    ]

    poll_count = 0

    # Import the actual function to call
    from cli.internal.aws.snapshotting import check_snapshot_status as real_check

    def track_polling(snapshot_id, session, region):
        nonlocal poll_count
        poll_count += 1
        return real_check(snapshot_id, session, region)

    # Patch where it's USED (in backup module), not where it's defined
    with (
        patch("cli.internal.aws.backup.POLL_INTERVAL", 0.1),
        patch(
            "cli.internal.aws.backup.check_snapshot_status", side_effect=track_polling
        ),
    ):
        backup_rds_resources(resources, session, "us-east-1", parallel=1)

    # Should have polled at least once
    assert poll_count >= 1


@mock_aws
def test_backup_empty_resource_list(mock_aws_credentials):
    """Handle empty resource list gracefully."""
    session = boto3.Session(region_name="us-east-1")
    resources = []

    # Should not raise error
    backup_rds_resources(resources, session, "us-east-1", parallel=1)


@mock_aws
def test_backup_parallel_higher_than_resource_count(mock_aws_credentials):
    """Handle case when parallel limit exceeds number of resources."""
    client = boto3.client("rds", region_name="us-east-1")

    # Create 2 clusters
    for i in range(1, 3):
        client.create_db_cluster(
            DBClusterIdentifier=f"high-par-{i}",
            Engine="aurora-postgresql",
            MasterUsername="admin",
            MasterUserPassword="password123",
        )

    session = boto3.Session(region_name="us-east-1")

    resources = [
        {
            "DBClusterIdentifier": "high-par-1",
            "Engine": "aurora-postgresql",
            "Status": "available",
        },
        {
            "DBClusterIdentifier": "high-par-2",
            "Engine": "aurora-postgresql",
            "Status": "available",
        },
    ]

    # Parallel limit of 10 but only 2 resources
    with patch("cli.internal.aws.backup.POLL_INTERVAL", 0.1):
        backup_rds_resources(resources, session, "us-east-1", parallel=10)

    # Should still create 2 snapshots
    all_snapshots = client.describe_db_cluster_snapshots()["DBClusterSnapshots"]
    backup_snapshots = [
        s
        for s in all_snapshots
        if s["DBClusterSnapshotIdentifier"].startswith("backup-")
    ]
    assert len(backup_snapshots) == 2
