import boto3

def get_client(service_name: str):
    """Create and return a boto3 client for the specified AWS service."""
    return boto3.client(service_name)
    