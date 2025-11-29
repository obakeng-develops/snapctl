import pytest
from moto import mock_aws
import boto3
from botocore.exceptions import ClientError

from cli.internal.aws.snapshotting import (
    create_cluster_snapshot,
    check_snapshot_status,
    initiate_snapshot,
)


@pytest.fixture
def mock_rds_cluster():
    """Create a mock RDS Aurora cluster for testing."""
    with mock_aws():
        client = boto3.client("rds", region_name="us-east-1")

        # Create a mock Aurora cluster
        client.create_db_cluster(
            DBClusterIdentifier="test-cluster",
            Engine="aurora-postgresql",
            MasterUsername="admin",
            MasterUserPassword="password123",
            Tags=[
                {"Key": "Environment", "Value": "test"},
                {"Key": "Owner", "Value": "devops"},
            ],
        )

        yield client


class TestCreateClusterSnapshot:
    """Test snapshot creation."""

    def test_create_snapshot_success(self, mock_aws_credentials, mock_rds_cluster):
        """Successfully create a cluster snapshot."""
        session = boto3.Session(region_name="us-east-1")

        result = create_cluster_snapshot(
            cluster_id="test-cluster",
            prefix="backup",
            session=session,
            region="us-east-1",
        )

        # Verify snapshot was created
        assert "DBClusterSnapshotIdentifier" in result
        assert result["DBClusterSnapshotIdentifier"].startswith("backup-test-cluster")
        assert "DBClusterSnapshotArn" in result
        assert "test-cluster" in result["DBClusterSnapshotArn"]

    def test_create_snapshot_applies_tags(self, mock_aws_credentials, mock_rds_cluster):
        """Snapshot should have correct tags."""
        session = boto3.Session(region_name="us-east-1")

        result = create_cluster_snapshot(
            cluster_id="test-cluster",
            prefix="test",
            session=session,
            region="us-east-1",
        )

        # Check that tags were applied
        client = session.client("rds", region_name="us-east-1")
        tags_response = client.list_tags_for_resource(
            ResourceName=result["DBClusterSnapshotArn"]
        )

        tag_dict = {tag["Key"]: tag["Value"] for tag in tags_response["TagList"]}

        assert tag_dict.get("origin") == "snapctl"
        assert tag_dict.get("resource") == "test-cluster"
        assert tag_dict.get("prefix") == "test"
        assert tag_dict.get("version") == "0.1.0"
        assert "createdAt" in tag_dict

    def test_create_snapshot_nonexistent_cluster(self, mock_aws_credentials):
        """Creating snapshot for nonexistent cluster should raise error."""
        with mock_aws():
            session = boto3.Session(region_name="us-east-1")

            with pytest.raises(Exception):
                create_cluster_snapshot(
                    cluster_id="nonexistent-cluster",
                    prefix="backup",
                    session=session,
                    region="us-east-1",
                )

    def test_snapshot_id_includes_timestamp(
        self, mock_aws_credentials, mock_rds_cluster
    ):
        """Snapshot ID should include timestamp for uniqueness."""
        import time

        session = boto3.Session(region_name="us-east-1")

        result1 = create_cluster_snapshot(
            cluster_id="test-cluster",
            prefix="backup",
            session=session,
            region="us-east-1",
        )

        time.sleep(1)

        result2 = create_cluster_snapshot(
            cluster_id="test-cluster",
            prefix="backup",
            session=session,
            region="us-east-1",
        )

        # Should have different IDs due to timestamp
        assert (
            result1["DBClusterSnapshotIdentifier"]
            != result2["DBClusterSnapshotIdentifier"]
        )


class TestCheckSnapshotStatus:
    """Test snapshot status checking."""

    def test_check_status_success(self, mock_aws_credentials, mock_rds_cluster):
        """Check status of an existing snapshot."""
        session = boto3.Session(region_name="us-east-1")

        # Create a snapshot first
        snapshot = create_cluster_snapshot(
            cluster_id="test-cluster",
            prefix="test",
            session=session,
            region="us-east-1",
        )

        snapshot_id = snapshot["DBClusterSnapshotIdentifier"]

        # Check its status
        status = check_snapshot_status(snapshot_id, session, "us-east-1")

        # Status should be one of the valid RDS snapshot statuses
        assert status in ["creating", "available", "deleting", "failed"]

    def test_check_status_nonexistent_snapshot(self, mock_aws_credentials):
        """Checking nonexistent snapshot should raise error."""
        with mock_aws():
            session = boto3.Session(region_name="us-east-1")

            with pytest.raises(ClientError):
                check_snapshot_status("nonexistent-snapshot", session, "us-east-1")


class TestInitiateSnapshot:
    """Test the initiate_snapshot function."""

    def test_initiate_snapshot_success(self, mock_aws_credentials, mock_rds_cluster):
        """Successfully initiate a snapshot."""
        session = boto3.Session(region_name="us-east-1")

        resource = {
            "DBClusterIdentifier": "test-cluster",
            "Engine": "aurora-postgresql",
            "Status": "available",
        }

        result = initiate_snapshot(resource, session, "us-east-1")

        # Should return snapshot info (note: your current implementation doesn't return,
        # but it should - this test assumes the fix)
        # If not fixed yet, you'll need to update the function
        assert result is not None
