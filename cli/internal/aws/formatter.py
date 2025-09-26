from typing import Any
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich import box
import re

def format_scheduling_config(config:dict):
    schedule = config["protect"]["schedule"]
    retention = config["protect"]["retention"]
    
    # Parse schedule
    schedule_match = re.match(r'^(daily|weekly|monthly)@(\d+)(am|pm)$', schedule, re.IGNORECASE)
    if not schedule_match:
        raise ValueError('Invalid schedule format')
    
    frequency, hour, period = schedule_match.groups()
    hour = int(hour)
    
    # Convert to 24-hour format
    if period.lower() == 'pm' and hour != 12:
        hour_24 = hour + 12
    elif period.lower() == 'am' and hour == 12:
        hour_24 = 0
    else:
        hour_24 = hour
    
    schedule_text = f"{frequency.capitalize()} backups at {hour_24}:00 UTC"
    
    # Parse retention
    retention_match = re.match(r'^(\d+)([dwmy])$', retention)
    if not retention_match:
        raise ValueError('Invalid retention format')
    
    amount, unit = retention_match.groups()
    amount = int(amount)
    
    unit_map = {
        'd': 'day',
        'w': 'week',
        'm': 'month',
        'y': 'year'
    }
    
    unit_name = unit_map[unit] + ('s' if amount > 1 else '')
    retention_text = f"Retain for {amount} {unit_name}"
    
    return {
        'schedule': schedule_text,
        'retention': retention_text
    }

def format_rds_cluster(config: dict, instances: list[dict[str, Any]]):
    """Format RDS cluster data for terminal display with only important info"""
    app_name = config["app"]
    region = config["provider"]["region"]
    scheduling_text = format_scheduling_config(config)
    resource_name = config["protect"]["resources"][0]["name"]
    tags = config["protect"]["resources"][0]["discover"]
    auth = config["auth"]
    
    console = Console()

    if "profile" in auth:
        # Header Panel
        header = Panel(
            f"[bold cyan]App:[/bold cyan] {app_name}\n"
            f"[bold cyan]Region:[/bold cyan] {region}\n"
            f"[bold cyan]Profile:[/bold cyan] {auth["profile"]}",
            title="[bold white]Backup Plan Preview[/bold white]",
            border_style="cyan",
            box=box.ROUNDED
        )
        console.print(header)
        console.print()
    else:
        # Header Panel
        header = Panel(
            f"[bold cyan]App:[/bold cyan] {app_name}\n"
            f"[bold cyan]Region:[/bold cyan] {region}\n"
            f"[bold cyan]Role ARN:[/bold cyan] {auth["role_arn"]}",
            title="[bold white]Backup Plan Preview[/bold white]",
            border_style="cyan",
            box=box.ROUNDED
        )
        console.print(header)
        console.print()

    # Schedule & Retention
    console.print("[bold]📋 Schedule & Retention[/bold]")
    console.print(f"   [dim]•[/dim] {scheduling_text["schedule"]}")
    console.print(f"   [dim]•[/dim] {scheduling_text["retention"]}")
    console.print()

    # Resources Tree
    console.print("[bold]🗄️  Resources to Backup[/bold]")
    console.print()

    tree = Tree(
        f"[bold cyan]RDS Instances[/bold cyan] [dim]({resource_name})[/dim]",
        guide_style="dim"
    )
    tree.add(f"[dim]Filter:[/dim] {tags}")
    found_branch = tree.add(f"[green]Found: {len(instances)} instances[/green]")
    for instance in instances:
        found_branch.add(f"[cyan]{instance['DBInstanceIdentifier']}[/cyan] [dim]({instance['DBInstanceClass']})[/dim]")

    console.print(tree)
    console.print()

    # Success message
    console.print("[bold green]✓[/bold green] Plan is valid. Run with [bold]snapctl run -c[/bold] to apply.")
