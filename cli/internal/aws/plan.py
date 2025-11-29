import boto3
import structlog
from .client import get_client
from .formatter import format_rds_resources
from .resource_filtering import list_resource_by_tag

logger = structlog.get_logger()


def aws_plan(config: dict, session: boto3.Session):
    """Generate a backup plan showing all resources that will be backed up."""
    region = config["provider"]["region"]
    app_name = config["app"]
    auth = config["auth"]

    # Display header once
    from rich.console import Console
    from rich.panel import Panel
    from rich import box

    console = Console()

    auth_display = (
        f"Profile: {auth['profile']}"
        if "profile" in auth
        else f"Role: {auth['role_arn']}"
    )

    header = Panel(
        f"[bold cyan]App:[/bold cyan] {app_name}\n"
        f"[bold cyan]Region:[/bold cyan] {region}\n"
        f"[bold cyan]Auth:[/bold cyan] {auth_display}",
        title="[bold white]Backup Plan Preview[/bold white]",
        border_style="cyan",
        box=box.ROUNDED,
    )
    console.print(header)
    console.print()

    # Process each resource configuration
    all_resources = []
    for resource_config in config["backup"]["resources"]:
        service_type = resource_config["type"]
        resource_name = resource_config["name"]
        tags = resource_config["discover"]

        logger.info(f"Discovering {service_type} resources: {resource_name}")

        client = get_client(service_type, session, region)
        resources = list_resource_by_tag(client, service_type, tags)

        all_resources.append(
            {
                "type": service_type,
                "name": resource_name,
                "tags": tags,
                "resources": resources,
            }
        )

    # Format output based on resource types
    for resource_group in all_resources:
        match resource_group["type"]:
            case "rds":
                format_rds_resources(resource_group)
            case "ebs":
                console.print("[yellow]⚠[/yellow] EBS support coming soon")
            case _:
                console.print(
                    f"[yellow]⚠[/yellow] Unsupported resource type: {resource_group['type']}"
                )

    # Summary
    total_resources = sum(len(rg["resources"]) for rg in all_resources)
    console.print()
    if total_resources > 0:
        console.print(
            f"[bold green]✓[/bold green] Plan is valid. Found {total_resources} resource(s) to backup."
        )
        console.print(
            "[dim]Run[/dim] [bold]snapctl backup --config <file>[/bold] [dim]to execute[/dim]"
        )
    else:
        console.print(
            "[bold yellow]⚠[/bold yellow] No resources found matching the filters."
        )
