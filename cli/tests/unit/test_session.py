from datetime import datetime
from cli.internal.aws.session import generate_session_name


class TestGenerateSessionName:
    """Test session name generation."""
    
    def test_generate_session_name_format(self):
        """Session name should have correct format."""
        app_name = "my-app"
        result = generate_session_name(app_name)
        
        # Should start with app name
        assert result.startswith("my-app-backup-")
        
        # Should contain timestamp
        assert len(result) > len("my-app-backup-")
    
    def test_generate_session_name_timestamp(self):
        """Session name should contain valid timestamp."""
        app_name = "test"
        result = generate_session_name(app_name)
        
        # Extract timestamp part
        timestamp_part = result.replace("test-backup-", "")
        
        # Should be parseable as datetime
        datetime.strptime(timestamp_part, "%Y%m%d_%H%M%S")
    
    def test_generate_session_name_unique(self):
        """Session names should be unique (time-based)."""
        import time
        
        name1 = generate_session_name("app")
        time.sleep(1)  # Wait a second
        name2 = generate_session_name("app")
        
        assert name1 != name2
    
    def test_generate_session_name_different_apps(self):
        """Different apps should generate different names."""
        name1 = generate_session_name("app1")
        name2 = generate_session_name("app2")
        
        assert name1.startswith("app1")
        assert name2.startswith("app2")
