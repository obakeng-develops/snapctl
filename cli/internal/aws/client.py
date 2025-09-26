import boto3

def get_client(service_name: str, session: None, region: None = "us-east-1") -> boto3.client:
    """Create and return a boto3 client for the specified AWS service."""
    if session:
        return session.client(service_name, region)
    else:
        return boto3.client(service_name)
    