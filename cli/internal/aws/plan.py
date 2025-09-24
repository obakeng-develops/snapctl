from .client import get_client

def aws_plan(config: dict):
    service = config["protect"]["resources"][0]["type"]
    
    client = get_client(service)
    
    print(client)
