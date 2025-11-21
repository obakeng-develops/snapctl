import boto3
from .client import get_client
from .formatter import format_rds_cluster
from .resource_filtering import list_resource_by_tag

def aws_plan(config: dict, session: boto3.Session):
    service = config["backup"]["resources"][0]["type"]
    region = config["provider"]["region"]
    tags = config["backup"]["resources"][0]["discover"]
    
    client = get_client(service, session, region)
    
    resources = list_resource_by_tag(client, service, tags)

    match service:
        case "rds":
            format_rds_cluster(config, resources)
