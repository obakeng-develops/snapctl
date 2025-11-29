import pytest
import yaml


@pytest.fixture
def sample_config():
    """Standard test configuration."""
    return {
        "app": "test-app",
        "provider": {
            "name": "aws",
            "region": "us-east-1"
        },
        "auth": {
            "profile": "test-profile"
        },
        "backup": {
            "resources": [
                {
                    "type": "rds",
                    "name": "production-databases",
                    "tags": "tag:Environment=prod"
                }
            ]
        }
    }


@pytest.fixture
def config_file(tmp_path, sample_config):
    """Create a temporary config file."""
    config_path = tmp_path / "test-config.yml"
    config_path.write_text(yaml.dump(sample_config))
    return str(config_path)


@pytest.fixture
def mock_aws_credentials(monkeypatch):
    """Mock AWS credentials to prevent actual AWS calls."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
