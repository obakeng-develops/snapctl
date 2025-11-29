from typing import Any
from rich.console import Console
from rich.tree import Tree

console = Console()


def format_rds_resources(resource_group: dict[str, Any]):
    """Format RDS resources for terminal display."""
    resource_name = resource_group["name"]
    tags = resource_group["tags"]
    resources = resource_group["resources"]

    console.print(f"[bold]🗄️  RDS Resources[/bold] [dim]({resource_name})[/dim]")

    tree = Tree(f"[bold cyan]Filter:[/bold cyan] {tags}", guide_style="dim")

    if not resources:
        tree.add("[yellow]No resources found[/yellow]")
    else:
        found_branch = tree.add(f"[green]Found: {len(resources)} resource(s)[/green]")

        for resource in resources:
            # Handle both DB instances and clusters
            if "DBInstanceIdentifier" in resource:
                identifier = resource["DBInstanceIdentifier"]
                instance_class = resource.get("DBInstanceClass", "unknown")
                engine = resource.get("Engine", "unknown")
                status = resource.get("DBInstanceStatus", "unknown")

                status_color = "green" if status == "available" else "yellow"
                found_branch.add(
                    f"[cyan]Instance:[/cyan] {identifier} "
                    f"[dim]({instance_class}, {engine})[/dim] "
                    f"[{status_color}]{status}[/{status_color}]"
                )
            elif "DBClusterIdentifier" in resource:
                identifier = resource["DBClusterIdentifier"]
                engine = resource.get("Engine", "unknown")
                status = resource.get("Status", "unknown")

                status_color = "green" if status == "available" else "yellow"
                found_branch.add(
                    f"[cyan]Cluster:[/cyan] {identifier} "
                    f"[dim]({engine})[/dim] "
                    f"[{status_color}]{status}[/{status_color}]"
                )

    console.print(tree)
    console.print()
