import boto3
from .client import get_client
from .session import create_session_with_profile, create_session_with_role

def aws_plan(config: dict):
    service = config["protect"]["resources"][0]["type"]
    region = config["provider"]["region"]
    auth = config["auth"]
    
    # Determine authentication method
    if "role_arn" in auth:
        auth_type = "role"
        session = create_session_with_role(auth)
    elif "profile" in auth:
        auth_type = "profile"
        session = create_session_with_profile(auth)
    else:
        raise ValueError("No valid authentication method found in config")
    
    client = get_client(service, session, region)
    
    print(client)
