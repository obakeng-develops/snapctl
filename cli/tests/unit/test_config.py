import pytest
import yaml
from cli.internal.utility.config import read_config


class TestReadConfig:
    """Test configuration file reading."""
    
    def test_read_valid_config(self, tmp_path):
        """Read a valid YAML config file."""
        config_data = {
            "app": "test-app",
            "provider": {"name": "aws", "region": "us-east-1"}
        }
        config_file = tmp_path / "config.yml"
        config_file.write_text(yaml.dump(config_data))
        
        result = read_config(str(config_file))
        
        assert result["app"] == "test-app"
        assert result["provider"]["name"] == "aws"
    
    def test_read_nonexistent_file(self):
        """Reading nonexistent file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            read_config("nonexistent-config.yml")
    
    def test_read_none_path(self):
        """Passing None should raise ValueError."""
        with pytest.raises(ValueError, match="Config file path must be provided"):
            read_config(None)
    
    def test_read_empty_file(self, tmp_path):
        """Empty file should return None."""
        config_file = tmp_path / "empty.yml"
        config_file.write_text("")
        
        result = read_config(str(config_file))
        assert result is None
    
    def test_read_invalid_yaml(self, tmp_path):
        """Invalid YAML should raise error."""
        config_file = tmp_path / "invalid.yml"
        config_file.write_text("invalid: yaml: content: [[[")
        
        with pytest.raises(yaml.YAMLError):
            read_config(str(config_file))
    
    def test_read_complex_nested_config(self, tmp_path):
        """Read complex nested configuration."""
        config_data = {
            "app": "snapctl",
            "provider": {"name": "aws", "region": "us-west-2"},
            "backup": {
                "resources": [
                    {"type": "rds", "name": "db1", "tags": "tag:Env=prod"},
                    {"type": "ebs", "name": "vol1", "tags": "tag:Backup=true"}
                ]
            }
        }
        config_file = tmp_path / "config.yml"
        config_file.write_text(yaml.dump(config_data))
        
        result = read_config(str(config_file))
        
        assert len(result["backup"]["resources"]) == 2
        assert result["backup"]["resources"][0]["type"] == "rds"
