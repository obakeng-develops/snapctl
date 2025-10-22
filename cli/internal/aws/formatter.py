from typing import Any
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich import box
import re

def format_rds_cluster(config: dict, instances: list[dict[str, Any]]):
    """Format RDS cluster data for terminal display with only important info"""
    app_name = config["app"]
    region = config["provider"]["region"]
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
