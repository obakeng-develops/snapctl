import boto3
from .client import get_client
from .session import create_session_with_profile, create_session_with_role
from .formatter import format_rds_cluster
from .resource_filtering import list_resource_by_tag

def aws_plan(config: dict):
    service = config["protect"]["resources"][0]["type"]
    region = config["provider"]["region"]
    auth = config["auth"]
    tags = config["protect"]["resources"][0]["discover"]
    
    if "role_arn" in auth:
        session = create_session_with_role(auth)
    elif "profile" in auth:
        session = create_session_with_profile(auth)
    else:
        raise ValueError("No valid authentication method found in config")
    
    client = get_client(service, session, region)
    
    instances = list_resource_by_tag(client, service, tags)

    match service:
        case "rds":
            format_rds_cluster(instances)
