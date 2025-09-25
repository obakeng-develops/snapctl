import boto3
from .client import get_client
from .session import create_session_with_profile, create_session_with_role
from .formatter import format_rds_cluster

def aws_plan(config: dict):
    service = config["protect"]["resources"][0]["type"]
    region = config["provider"]["region"]
    auth = config["auth"]
    
    if "role_arn" in auth:
        session = create_session_with_role(auth)
    elif "profile" in auth:
        session = create_session_with_profile(auth)
    else:
        raise ValueError("No valid authentication method found in config")
    
    client = get_client(service, session, region)
    
    db_cluster = client.describe_db_clusters(
        DBClusterIdentifier=config["protect"]["resources"][0]["identifier"]
    )
    
    if db_cluster is None:
        raise ValueError("No DB cluster found with the specified identifier")

    match service:
        case "rds":
            format_rds_cluster(db_cluster)
