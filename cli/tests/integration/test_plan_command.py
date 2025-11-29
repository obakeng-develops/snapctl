"""Integration tests for plan command - shows actual formatted output."""
import pytest
from moto import mock_aws
import boto3
from typer.testing import CliRunner
from unittest.mock import patch
from cli.commands.plan import app

runner = CliRunner()


@mock_aws
@patch('cli.commands.plan.create_session')
def test_plan_single_resource_with_instances(mock_session, mock_aws_credentials, tmp_path):
    """Test plan command with RDS instances - see the output!"""
    # Mock session to return a real mocked boto3 session
    mock_session.return_value = boto3.Session(region_name="us-east-1")
    
    # Create mock RDS instances
    client = boto3.client("rds", region_name="us-east-1")
    
    # Create 3 production databases
    for i in range(1, 4):
        client.create_db_instance(
            DBInstanceIdentifier=f"prod-db-{i}",
            DBInstanceClass="db.t3.medium",
            Engine="postgres",
            MasterUsername="admin",
            MasterUserPassword="password123",
            Tags=[
                {"Key": "Environment", "Value": "prod"},
                {"Key": "Team", "Value": "backend"}
            ]
        )
    
    # Create config
    config_content = """
app: "my-awesome-app"

provider:
  name: aws
  region: us-east-1

auth:
  profile: "dev-profile"

backup:
  resources:
    - type: rds
      name: production-databases
      discover: "tag:Environment=prod"
"""
    
    config_path = tmp_path / "test-config.yml"
    config_path.write_text(config_content)
    
    # Run plan command
    result = runner.invoke(app, ["--config", str(config_path)])
    
    # Show the output
    print("\n" + "="*60)
    print("PLAN OUTPUT:")
    print("="*60)
    print(result.stdout)
    print("="*60 + "\n")
    
    # Assertions
    assert result.exit_code == 0
    assert "my-awesome-app" in result.stdout
    assert "production-databases" in result.stdout
    assert "prod-db-1" in result.stdout
    assert "prod-db-2" in result.stdout
    assert "prod-db-3" in result.stdout
    assert "Found: 3 resource(s)" in result.stdout


@mock_aws
@patch('cli.commands.plan.create_session')
def test_plan_multiple_resources(mock_session, mock_aws_credentials, tmp_path):
    """Test plan with multiple resource groups."""
    mock_session.return_value = boto3.Session(region_name="us-east-1")
    
    client = boto3.client("rds", region_name="us-east-1")
    
    # Create production databases
    client.create_db_instance(
        DBInstanceIdentifier="prod-api-db",
        DBInstanceClass="db.r5.large",
        Engine="postgres",
        MasterUsername="admin",
        MasterUserPassword="password123",
        Tags=[
            {"Key": "Environment", "Value": "prod"},
            {"Key": "Service", "Value": "api"}
        ]
    )
    
    # Create staging databases
    client.create_db_instance(
        DBInstanceIdentifier="staging-api-db",
        DBInstanceClass="db.t3.small",
        Engine="mysql",
        MasterUsername="admin",
        MasterUserPassword="password123",
        Tags=[
            {"Key": "Environment", "Value": "staging"},
            {"Key": "Service", "Value": "api"}
        ]
    )
    
    # Config with multiple resources
    config_content = """
app: "multi-env-app"

provider:
  name: aws
  region: us-east-1

auth:
  profile: "prod-profile"

backup:
  resources:
    - type: rds
      name: production-databases
      discover: "tag:Environment=prod"
    - type: rds
      name: staging-databases
      discover: "tag:Environment=staging"
"""
    
    config_path = tmp_path / "multi-config.yml"
    config_path.write_text(config_content)
    
    # Run plan
    result = runner.invoke(app, ["--config", str(config_path)])
    
    print("\n" + "="*60)
    print("MULTIPLE RESOURCES PLAN OUTPUT:")
    print("="*60)
    print(result.stdout)
    print("="*60 + "\n")
    
    assert result.exit_code == 0
    assert "production-databases" in result.stdout
    assert "staging-databases" in result.stdout
    assert "prod-api-db" in result.stdout
    assert "staging-api-db" in result.stdout


@mock_aws
@patch('cli.commands.plan.create_session')
def test_plan_no_resources_found(mock_session, mock_aws_credentials, tmp_path):
    """Test plan when no resources match the filter."""
    mock_session.return_value = boto3.Session(region_name="us-east-1")
    
    # Don't create any RDS instances
    
    config_content = """
app: "empty-app"

provider:
  name: aws
  region: us-east-1

auth:
  profile: "test-profile"

backup:
  resources:
    - type: rds
      name: nonexistent-databases
      discover: "tag:DoesNotExist=nope"
"""
    
    config_path = tmp_path / "empty-config.yml"
    config_path.write_text(config_content)
    
    result = runner.invoke(app, ["--config", str(config_path)])
    
    print("\n" + "="*60)
    print("NO RESOURCES FOUND OUTPUT:")
    print("="*60)
    print(result.stdout)
    print("="*60 + "\n")
    
    assert result.exit_code == 0
    assert "No resources found" in result.stdout or "0 resource(s)" in result.stdout


@mock_aws
@patch('cli.commands.plan.create_session')
def test_plan_with_clusters(mock_session, mock_aws_credentials, tmp_path):
    """Test plan with Aurora clusters."""
    mock_session.return_value = boto3.Session(region_name="us-east-1")
    
    client = boto3.client("rds", region_name="us-east-1")
    
    # Create Aurora cluster
    client.create_db_cluster(
        DBClusterIdentifier="prod-aurora-cluster",
        Engine="aurora-mysql",  # Use aurora-mysql which moto supports
        MasterUsername="admin",
        MasterUserPassword="password123",
        Tags=[
            {"Key": "Environment", "Value": "prod"},
            {"Key": "Type", "Value": "aurora"}
        ]
    )
    
    config_content = """
app: "aurora-app"

provider:
  name: aws
  region: us-east-1

auth:
  profile: "aurora-profile"

backup:
  resources:
    - type: rds
      name: aurora-clusters
      discover: "tag:Type=aurora"
"""
    
    config_path = tmp_path / "aurora-config.yml"
    config_path.write_text(config_content)
    
    result = runner.invoke(app, ["--config", str(config_path)])
    
    print("\n" + "="*60)
    print("AURORA CLUSTER PLAN OUTPUT:")
    print("="*60)
    print(result.stdout)
    print("="*60 + "\n")
    
    assert result.exit_code == 0
    assert "prod-aurora-cluster" in result.stdout
    assert "Cluster:" in result.stdout  # Should show as "Cluster" not "Instance"


@mock_aws
@patch('cli.commands.plan.create_session')
def test_plan_with_mixed_status(mock_session, mock_aws_credentials, tmp_path):
    """Test plan showing resources with different statuses."""
    mock_session.return_value = boto3.Session(region_name="us-east-1")
    
    client = boto3.client("rds", region_name="us-east-1")
    
    # Create instances with different statuses
    client.create_db_instance(
        DBInstanceIdentifier="available-db",
        DBInstanceClass="db.t3.micro",
        Engine="postgres",
        MasterUsername="admin",
        MasterUserPassword="password123",
        Tags=[{"Key": "Test", "Value": "status"}]
    )
    
    config_content = """
app: "status-test"

provider:
  name: aws
  region: us-east-1

auth:
  profile: "test"

backup:
  resources:
    - type: rds
      name: all-databases
      discover: "tag:Test=status"
"""
    
    config_path = tmp_path / "status-config.yml"
    config_path.write_text(config_content)
    
    result = runner.invoke(app, ["--config", str(config_path)])
    
    print("\n" + "="*60)
    print("MIXED STATUS PLAN OUTPUT:")
    print("="*60)
    print(result.stdout)
    print("="*60 + "\n")
    
    assert result.exit_code == 0
    assert "available-db" in result.stdout

@mock_aws
@patch('cli.commands.plan.create_session')
def test_plan_with_mixed_instances_and_clusters(mock_session, mock_aws_credentials, tmp_path):
    """Test plan finding both DB instances AND clusters."""
    mock_session.return_value = boto3.Session(region_name="us-east-1")
    
    client = boto3.client("rds", region_name="us-east-1")
    
    # Create a regular RDS instance
    client.create_db_instance(
        DBInstanceIdentifier="prod-postgres-instance",
        DBInstanceClass="db.t3.small",
        Engine="postgres",
        MasterUsername="admin",
        MasterUserPassword="password123",
        Tags=[
            {"Key": "Environment", "Value": "prod"},
            {"Key": "App", "Value": "api"}
        ]
    )
    
    # Create an Aurora cluster
    client.create_db_cluster(
        DBClusterIdentifier="prod-aurora-cluster",
        Engine="aurora-mysql",
        MasterUsername="admin",
        MasterUserPassword="password123",
        Tags=[
            {"Key": "Environment", "Value": "prod"},
            {"Key": "App", "Value": "api"}
        ]
    )
    
    config_content = """
app: "mixed-resources-app"

provider:
  name: aws
  region: us-east-1

auth:
  profile: "test-profile"

backup:
  resources:
    - type: rds
      name: all-production-databases
      discover: "tag:Environment=prod AND tag:App=api"
"""
    
    config_path = tmp_path / "mixed-config.yml"
    config_path.write_text(config_content)
    
    result = runner.invoke(app, ["--config", str(config_path)])
    
    print("\n" + "="*60)
    print("MIXED INSTANCES AND CLUSTERS OUTPUT:")
    print("="*60)
    print(result.stdout)
    print("="*60 + "\n")
    
    assert result.exit_code == 0
    assert "prod-postgres-instance" in result.stdout
    assert "prod-aurora-cluster" in result.stdout
    assert "Found: 2 resource(s)" in result.stdout
    assert "Instance:" in result.stdout  # Should show one instance
    assert "Cluster:" in result.stdout   # Should show one cluster
