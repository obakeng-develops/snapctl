import boto3
from datetime import datetime

def generate_session_name(app_name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return f"{app_name}-backup-{timestamp}"

def create_session_with_role(auth_config: dict) -> boto3.Session:
    """Create session by assuming role"""
    app_name = auth_config["app"]
    
    if "profile" in auth_config:
        session = boto3.Session(profile_name=auth_config["profile"])
        sts_client = session.Client('sts')
    else:
        sts_client = boto3.client('sts')
        
    # Assume the role
    response = sts_client.assume_role(
        RoleArn=auth_config["role_arn"],
        RoleSessionName=generate_session_name(app_name)
    )
    
    credentials = response['credentials']
    
    return boto3.Session(
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )

def create_session_with_profile(auth_config):
    """Create session with a named profile"""
    return boto3.Session(profile_name=auth_config["profile"])
