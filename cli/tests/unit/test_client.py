import pytest
import boto3
from unittest.mock import Mock, patch
from cli.internal.aws.client import get_client


class TestGetClient:
    """Test AWS client creation."""
    
    def test_get_client_with_session(self):
        """Create client using provided session."""
        mock_session = Mock(spec=boto3.Session)
        mock_client = Mock()
        mock_session.client.return_value = mock_client
        
        result = get_client("rds", mock_session, "us-west-2")
        
        # Should call session.client with service and region
        mock_session.client.assert_called_once_with("rds", "us-west-2")
        assert result == mock_client
    
    def test_get_client_without_session(self):
        """Create client without session (uses default credentials)."""
        with patch('boto3.client') as mock_boto_client:
            mock_client = Mock()
            mock_boto_client.return_value = mock_client
            
            result = get_client("rds", None, "us-east-1")
            
            # Should use boto3.client directly
            mock_boto_client.assert_called_once_with("rds")
            assert result == mock_client
    
    def test_get_client_different_services(self):
        """Create clients for different AWS services."""
        mock_session = Mock(spec=boto3.Session)
        
        # Test RDS
        get_client("rds", mock_session, "us-east-1")
        mock_session.client.assert_called_with("rds", "us-east-1")
        
        # Test EC2
        get_client("ec2", mock_session, "us-east-1")
        mock_session.client.assert_called_with("ec2", "us-east-1")
        
        # Test STS
        get_client("sts", mock_session, "us-east-1")
        mock_session.client.assert_called_with("sts", "us-east-1")
    
    def test_get_client_different_regions(self):
        """Create clients for different regions."""
        mock_session = Mock(spec=boto3.Session)
        
        # Test different regions
        regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]
        
        for region in regions:
            get_client("rds", mock_session, region)
            mock_session.client.assert_called_with("rds", region)
