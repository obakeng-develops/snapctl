import boto3
from typing import Any

def parse_tag_filter(tag_string: str) -> list[list[tuple[str, str]]]:
    """
    Parse tag filter string into OR groups of AND conditions.
    Example: "tag:Owner=devops AND tag:Backup=true OR tag:Critical=yes"
    Returns: [[("Owner", "devops"), ("Backup", "true")], [("Critical", "yes")]]
    (Owner=devops AND Backup=true) OR (Critical=yes)
    """
    or_groups = []
    or_parts = tag_string.split(" OR ")
    
    for or_part in or_parts:
        and_conditions = []
        and_parts = or_part.split(" AND ")
        
        for and_part in and_parts:
            and_part = and_part.strip()
            if and_part.startswith("tag:"):
                tag_part = and_part[4:]
                key, value = tag_part.split("=", 1)
                and_conditions.append((key.strip(), value.strip()))
        
        if and_conditions:
            or_groups.append(and_conditions)
    
    return or_groups

def matches_tag_filter(resource_tags: list[dict[str, str]], or_groups: list[list[tuple[str, str]]]) -> bool:
    """
    Check if resource matches the tag filter.
    Returns True if ANY OR group is fully satisfied (all AND conditions in that group match).
    """
    resource_tag_dict = {tag['Key']: tag['Value'] for tag in resource_tags}
    
    # Check each OR group
    for and_conditions in or_groups:
        # Check if ALL AND conditions in this group match
        if all(resource_tag_dict.get(key) == value for key, value in and_conditions):
            return True  # This OR group matched
    
    return False  # No OR group matched

def list_resource_by_tag(client: boto3.client, service: str, tag_filter: str) -> list[dict[str, Any]]:
    """
    List resources matching the tag filter.
    tag_filter supports: "tag:Key=Value AND tag:Key2=Value2 OR tag:Key3=Value3"
    """
    matching_resources = []
    or_groups = parse_tag_filter(tag_filter)
    
    match service:
        case "rds":
            paginator = client.get_paginator('describe_db_instances')
        
            for page in paginator.paginate():
                for db in page['DBInstances']:
                    db_arn = db['DBInstanceArn']
                    tags_response = client.list_tags_for_resource(ResourceName=db_arn)
                        
                    if matches_tag_filter(tags_response['Tag_list'], or_groups):
                        matching_resources.append(db)
        case _:
            raise ValueError(f"Unsupported service: {service}")
        
    return matching_resources
