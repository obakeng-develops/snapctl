import boto3
from typing import Any, Optional


def get_client(
    service_name: str, 
    session: Optional[boto3.Session] = None, 
    region: str = "us-east-1"
) -> Any:
    """Create and return a boto3 client for the specified AWS service."""
    if session:
        return session.client(service_name, region_name=region)
    else:
        return boto3.client(service_name, region_name=region)
