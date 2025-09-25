import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.tree import Tree
from rich import box

def format_rds_cluster(cluster_data):
    """Format RDS cluster data for terminal display with only important info"""
    console = Console()

    # Header Panel
    header = Panel(
        "[bold cyan]App:[/bold cyan] facebook\n"
        "[bold cyan]Region:[/bold cyan] us-east-1\n"
        "[bold cyan]Profile:[/bold cyan] test",
        title="[bold white]Backup Plan Preview[/bold white]",
        border_style="cyan",
        box=box.ROUNDED
    )
    console.print(header)
    console.print()

    # Schedule & Retention
    console.print("[bold]📋 Schedule & Retention[/bold]")
    console.print("   [dim]•[/dim] Daily backups at 3:00 AM UTC")
    console.print("   [dim]•[/dim] Retain for 7 days")
    console.print()

    # Resources Tree
    console.print("[bold]🗄️  Resources to Backup[/bold]")
    console.print()

    tree = Tree(
        "[bold cyan]RDS Instances[/bold cyan] [dim](production-databases)[/dim]",
        guide_style="dim"
    )
    tree.add("[dim]Filter:[/dim] tag:Owner=devops")
    found_branch = tree.add("[green]Found: 3 instances[/green]")
    found_branch.add("[cyan]prod-db-01[/cyan] [dim](db.t3.medium)[/dim]")
    found_branch.add("[cyan]prod-db-02[/cyan] [dim](db.t3.medium)[/dim]")
    found_branch.add("[cyan]prod-db-03[/cyan] [dim](db.r5.large)[/dim]")

    console.print(tree)
    console.print()

    # Success message
    console.print("[bold green]✓[/bold green] Plan is valid. Run with [bold]--execute[/bold] to apply.")
