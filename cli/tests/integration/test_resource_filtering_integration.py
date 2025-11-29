import pytest
from moto import mock_aws
import boto3
from cli.internal.aws.resource_filtering import list_resource_by_tag


@pytest.fixture
def mock_rds_instances():
    """Create multiple mock RDS instances with various tags."""
    with mock_aws():
        client = boto3.client("rds", region_name="us-east-1")
        
        # Production database
        client.create_db_instance(
            DBInstanceIdentifier="prod-db-1",
            DBInstanceClass="db.t2.micro",
            Engine="postgres",
            MasterUsername="admin",
            MasterUserPassword="password123",
            Tags=[
                {"Key": "Environment", "Value": "prod"},
                {"Key": "Owner", "Value": "devops"},
                {"Key": "Backup", "Value": "true"}
            ]
        )
        
        # Another production database
        client.create_db_instance(
            DBInstanceIdentifier="prod-db-2",
            DBInstanceClass="db.t2.micro",
            Engine="mysql",
            MasterUsername="admin",
            MasterUserPassword="password123",
            Tags=[
                {"Key": "Environment", "Value": "prod"},
                {"Key": "Owner", "Value": "data-team"}
            ]
        )
        
        # Development database
        client.create_db_instance(
            DBInstanceIdentifier="dev-db-1",
            DBInstanceClass="db.t2.micro",
            Engine="postgres",
            MasterUsername="admin",
            MasterUserPassword="password123",
            Tags=[
                {"Key": "Environment", "Value": "dev"},
                {"Key": "Owner", "Value": "devops"}
            ]
        )
        
        # Critical database
        client.create_db_instance(
            DBInstanceIdentifier="critical-db-1",
            DBInstanceClass="db.t2.small",
            Engine="postgres",
            MasterUsername="admin",
            MasterUserPassword="password123",
            Tags=[
                {"Key": "Critical", "Value": "yes"},
                {"Key": "Owner", "Value": "finance"}
            ]
        )
        
        yield client


class TestResourceFilteringIntegration:
    """Test resource discovery with real AWS API calls (mocked)."""
    
    def test_list_by_single_tag(self, mock_aws_credentials, mock_rds_instances):
        """Find resources with a single tag match."""
        resources = list_resource_by_tag(
            mock_rds_instances, 
            "rds", 
            "tag:Environment=prod"
        )
        
        assert len(resources) == 2
        identifiers = [r["DBInstanceIdentifier"] for r in resources]
        assert "prod-db-1" in identifiers
        assert "prod-db-2" in identifiers
    
    def test_list_by_and_condition(self, mock_aws_credentials, mock_rds_instances):
        """Find resources matching AND condition (all tags must match)."""
        resources = list_resource_by_tag(
            mock_rds_instances,
            "rds",
            "tag:Environment=prod AND tag:Owner=devops"
        )
        
        # Only prod-db-1 has both Environment=prod AND Owner=devops
        assert len(resources) == 1
        assert resources[0]["DBInstanceIdentifier"] == "prod-db-1"
    
    def test_list_by_or_condition(self, mock_aws_credentials, mock_rds_instances):
        """Find resources matching OR condition (any group can match)."""
        resources = list_resource_by_tag(
            mock_rds_instances,
            "rds",
            "tag:Environment=dev OR tag:Critical=yes"
        )
        
        # Should find dev-db-1 (Environment=dev) and critical-db-1 (Critical=yes)
        assert len(resources) == 2
        identifiers = [r["DBInstanceIdentifier"] for r in resources]
        assert "dev-db-1" in identifiers
        assert "critical-db-1" in identifiers
    
    def test_list_by_complex_condition(self, mock_aws_credentials, mock_rds_instances):
        """Find resources with complex AND/OR combinations."""
        resources = list_resource_by_tag(
            mock_rds_instances,
            "rds",
            "tag:Environment=prod AND tag:Backup=true OR tag:Critical=yes"
        )
        
        # Should find:
        # - prod-db-1 (Environment=prod AND Backup=true)
        # - critical-db-1 (Critical=yes)
        assert len(resources) == 2
        identifiers = [r["DBInstanceIdentifier"] for r in resources]
        assert "prod-db-1" in identifiers
        assert "critical-db-1" in identifiers
    
    def test_list_no_matches(self, mock_aws_credentials, mock_rds_instances):
        """Return empty list when no resources match."""
        resources = list_resource_by_tag(
            mock_rds_instances,
            "rds",
            "tag:Environment=staging"
        )
        
        assert len(resources) == 0
    
    def test_list_all_resources_with_owner_tag(self, mock_aws_credentials, mock_rds_instances):
        """Find all resources with any Owner tag value."""
        # Test with OR to find different owners
        resources = list_resource_by_tag(
            mock_rds_instances,
            "rds",
            "tag:Owner=devops OR tag:Owner=data-team OR tag:Owner=finance"
        )
        
        # All 4 instances have an Owner tag
        assert len(resources) == 4
    
    def test_unsupported_service_raises_error(self, mock_aws_credentials, mock_rds_instances):
        """Unsupported service should raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported service: s3"):
            list_resource_by_tag(mock_rds_instances, "s3", "tag:Key=Value")
    
    def test_resource_includes_all_attributes(self, mock_aws_credentials, mock_rds_instances):
        """Returned resources should include all DB instance attributes."""
        resources = list_resource_by_tag(
            mock_rds_instances,
            "rds",
            "tag:Environment=prod"
        )
        
        resource = resources[0]
        
        # Check important attributes are present
        assert "DBInstanceIdentifier" in resource
        assert "DBInstanceClass" in resource
        assert "Engine" in resource
        assert "DBInstanceArn" in resource
        assert "DBInstanceStatus" in resource
