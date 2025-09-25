import typer
from rich.console import Console
from rich.table import Table
from rich import box
from datetime import datetime

def format_rds_cluster(cluster_data):
    """Format RDS cluster data for terminal display with only important info"""
    console = Console()
    
    # Create main info table
    table = Table(title="RDS Cluster Information", box=box.ROUNDED, show_header=True)
    table.add_column("Property", style="cyan", width=25)
    table.add_column("Value", style="white")
    
    # Extract important fields with better error handling
    engine = cluster_data.get('Engine', 'Unknown')
    engine_version = cluster_data.get('EngineVersion', '')
    engine_display = f"{engine} {engine_version}".strip() if engine != 'Unknown' else engine
    
    important_fields = {
        "Cluster ID": cluster_data.get('DBClusterIdentifier', 'Not found'),
        "Status": cluster_data.get('Status', 'Unknown'),
        "Engine": engine_display,
        "Endpoint": cluster_data.get('Endpoint', 'Not available'),
        "Reader Endpoint": cluster_data.get('ReaderEndpoint', 'Not available'),
        "Port": str(cluster_data.get('Port', 'Unknown')),
        "Multi-AZ": "Yes" if cluster_data.get('MultiAZ') else "No",
        "Encryption": "Yes" if cluster_data.get('StorageEncrypted') else "No",
        "Deletion Protection": "Yes" if cluster_data.get('DeletionProtection') else "No",
        "Backup Retention": f"{cluster_data.get('BackupRetentionPeriod', 'Unknown')} days",
        "Storage Type": cluster_data.get('StorageType', 'Not specified'),
    }
    
    # Add rows to table, only show meaningful values
    for key, value in important_fields.items():
        if value and str(value) not in ['Unknown', 'Not found', 'Not available', 'Not specified']:
            table.add_row(key, str(value))
    
    console.print(table)
    
    # Show cluster members in a separate table
    members = cluster_data.get('DBClusterMembers', [])
    if members:
        console.print("\n")
        members_table = Table(title="Cluster Members", box=box.ROUNDED)
        members_table.add_column("Instance ID", style="yellow")
        members_table.add_column("Role", style="green")
        members_table.add_column("Status", style="blue")
        
        for member in members:
            role = "Writer" if member.get('IsClusterWriter') else "Reader"
            status = member.get('DBClusterParameterGroupStatus', 'Unknown')
            members_table.add_row(
                member.get('DBInstanceIdentifier', ''),
                role,
                status
            )
        
        console.print(members_table)
    
    # Show serverless scaling config if present
    scaling_config = cluster_data.get('ServerlessV2ScalingConfiguration')
    if scaling_config:
        console.print("\n")
        scaling_table = Table(title="Serverless v2 Scaling", box=box.ROUNDED)
        scaling_table.add_column("Property", style="magenta")
        scaling_table.add_column("Value", style="white")
        
        scaling_table.add_row("Min Capacity", f"{scaling_config.get('MinCapacity')} ACU")
        scaling_table.add_row("Max Capacity", f"{scaling_config.get('MaxCapacity')} ACU")
        scaling_table.add_row("Auto Pause", f"{scaling_config.get('SecondsUntilAutoPause')}s")
        
        console.print(scaling_table)
