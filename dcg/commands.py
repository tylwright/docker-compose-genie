#!/usr/bin/env python3
import click
import subprocess
import yaml
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from .utils import load_deployments, save_deployments, start_deployment, stop_deployment, get_compose_file_path

@click.command()
@click.argument("name")
@click.argument("file_path")
@click.option('--start', is_flag=True, help='Start the deployment once added.')
def add(name, file_path, start):
    """
    \b
    Add a new deployment.

    NAME is the name of the deployment (ex. Plex).

    FILE_PATH is the directory containing the docker-compose file for the deployment (ex. /opt/apps/plex).
    """
    deployments = load_deployments()
    if any(deployment.get(name) for deployment in deployments):
        click.echo(f"Deployment {name} already exists.")
    else:
        deployments.append({name: {"file_path": file_path}})
        save_deployments(deployments)
        click.echo(f"Deployment {name} added.")
        if start:
            start_deployment(name, file_path)

@click.command()
@click.argument("name")
@click.option('--stop', is_flag=True, help='Stop the deployment before removing.')
def remove(name, stop):
    """
    \b
    Remove a deployment from dcg.

    NAME is the name of the deployment (ex. Plex).

    This command only removes the deployment from dcg and does not delete any actual data.
    """
    deployments = load_deployments()
    deployment_to_remove = None

    for deployment in deployments:
        if name in deployment:
            deployment_to_remove = deployment
            break

    if deployment_to_remove:
        if stop:
            file_path = deployment_to_remove[name]["file_path"]
            stop_deployment(name, file_path)
        
        deployments.remove(deployment_to_remove)
        save_deployments(deployments)
        click.echo(f"Deployment {name} removed from dcg.")
    else:
        click.echo(f"Deployment {name} not found.")

@click.command()
@click.argument("name")
@click.option("--start", is_flag=True, help='Start deployment once updated if not already running.')
@click.option("--restart", is_flag=True, help='Restarts deployment once updated.')
@click.pass_context
def update(ctx, name, start, restart):
    """
    \b
    Update a deployment by pulling new images and restarting.

    NAME is the name of the deployment (ex. Plex).

    Only one of --start or --restart can be used at a time.
    """
    if start and restart:
        ctx.fail("You cannot use both --start and --restart options together.")

    deployments = load_deployments()
    deployment_to_update = None

    for deployment in deployments:
        if name in deployment:
            deployment_to_update = deployment[name]
            break

    if deployment_to_update:
        file_path = deployment_to_update.get("file_path", "N/A")
        compose_file = get_compose_file_path(file_path)

        if compose_file:
            # Pull new images and bring up the updated deployment
            subprocess.run(["docker", "compose", "-f", compose_file, "pull"])
            if restart:
                stop_deployment(name, file_path)
                start_deployment(name, file_path)
            elif start:
                start_deployment(name, file_path)
            else:
                click.echo(f"Deployment {name} updated without starting or restarting.")
        else:
            click.echo(f"No docker-compose file found in {file_path}.")
    else:
        click.echo(f"Deployment {name} not found.")

@click.command()
@click.argument("name")
def up(name):
    """
    \b
    Start a deployment.

    NAME is the name of the deployment (ex. Plex).
    """
    deployments = load_deployments()

    for deployment in deployments:
        if name in deployment:
            file_path = deployment[name].get("file_path", "N/A")
            start_deployment(name, file_path)
            break
    else:
        click.echo(f"Deployment {name} not found.")

@click.command()
@click.argument("name")
def down(name):
    """
    \b
    Stop a deployment.

    NAME is the name of the deployment (ex. Plex).
    """
    deployments = load_deployments()

    for deployment in deployments:
        if name in deployment:
            file_path = deployment[name].get("file_path", "N/A")
            stop_deployment(name, file_path)
            break
    else:
        click.echo(f"Deployment {name} not found.")

@click.command()
@click.argument("name")
def restart(name):
    """
    \b
    Restart a deployment.

    NAME is the name of the deployment (ex. Plex).
    """
    deployments = load_deployments()

    for deployment in deployments:
        if name in deployment:
            file_path = deployment[name].get("file_path", "N/A")
            stop_deployment(name, file_path)
            start_deployment(name, file_path)
            break
    else:
        click.echo(f"Deployment {name} not found.")

@click.command()
@click.option('--show-file-path', '-s', is_flag=True, help='Show directory where docker-compose.yaml is located.')
@click.option('--show-raw', '-r', is_flag=True, help='Show raw deployments.json content.')
def list_deployments(show_file_path, show_raw):
    """
    List all deployments, sorted alphabetically, showing their name, file path (optional), and current status.
    Optionally show raw content of deployments.json.
    """
    deployments = load_deployments()
    console = Console()

    if show_raw:
        # Print the deployments as nicely formatted YAML
        console.print(yaml.dump({'deployments': deployments}, default_flow_style=False, sort_keys=False, indent=2))
        return

    if deployments:
        # Create a Rich Table
        table = Table(title="Deployments Status")

        # Add columns based on whether file path should be shown
        table.add_column("Name", style="cyan", no_wrap=True)
        if show_file_path:
            table.add_column("File Path", style="magenta")
        table.add_column("Status", justify="right", style="green")

        # Populate the table with data
        for deployment in sorted(deployments, key=lambda x: list(x.keys())[0]):
            name = list(deployment.keys())[0]
            file_path = deployment[name].get("file_path", "N/A")
            compose_file = get_compose_file_path(file_path)

            if compose_file:
                result = subprocess.run(["docker", "compose", "-f", compose_file, "ps", "--quiet"], capture_output=True, text=True)
                status = "Up" if result.stdout.strip() else "Down"
            else:
                status = "N/A"

            # Apply conditional styling to the status
            status_style = "red" if status == "Down" else "green"

            if show_file_path:
                table.add_row(name, file_path, status, style=status_style)
            else:
                table.add_row(name, status, style=status_style)

        # Print the table using Rich's Console
        console.print(table)
    else:
        console.print("No deployments found.", style="bold red")

@click.command()
@click.option("--force", is_flag=True, help="Force stop all deployments without confirmation.")
def stop_all(force):
    """
    Stop all deployments.
    """
    if force or click.confirm("Are you sure you want to stop all deployments?"):
        deployments = load_deployments()
        for name, data in deployments.items():
            file_path = data["file_path"]
            stop_deployment(name, file_path)
    else:
        click.echo("Action canceled.")

@click.command()
@click.option("--force", is_flag=True, help="Force start all deployments without confirmation.")
def start_all(force):
    """
    Start all deployments.
    """
    if force or click.confirm("Are you sure you want to start all deployments?"):
        deployments = load_deployments()
        for name, data in deployments.items():
            file_path = data["file_path"]
            start_deployment(name, file_path)
    else:
        click.echo("Action canceled.")

@click.command()
@click.argument("name")
@click.option('--list-containers', '-l', is_flag=True, help='List individual containers and their status.')
def status(name, list_containers):
    """
    Check the status of a specific deployment.

    NAME is the name of the deployment (ex. Plex).
    """
    deployments = load_deployments()
    deployment_to_check = None
    console = Console()

    for deployment in deployments:
        if name in deployment:
            deployment_to_check = deployment[name]
            break

    if deployment_to_check:
        file_path = deployment_to_check.get("file_path", "N/A")
        compose_file = get_compose_file_path(file_path)

        if compose_file:
            if list_containers:
                # Get detailed information about each container
                ps_result = subprocess.run(
                    ["docker", "compose", "-f", compose_file, "ps"],
                    capture_output=True, text=True)
                lines = ps_result.stdout.splitlines()

                tree = Tree(f"[bold cyan]{name}[/bold cyan]")

                if len(lines) > 1:
                    for line in lines[1:]:  # Skip header line
                        parts = line.split()
                        container_name = parts[0]

                        # Get detailed information about the container
                        inspect_result = subprocess.run(
                            ["docker", "inspect", container_name],
                            capture_output=True, text=True)
                        container_info = yaml.safe_load(inspect_result.stdout)[0]

                        ports = container_info.get('NetworkSettings', {}).get('Ports', {})
                        ports_str = ', '.join([f"{k}:{v[0]['HostPort']}" for k, v in ports.items() if v])

                        image = container_info.get('Config', {}).get('Image', 'N/A')

                        # Calculate uptime
                        started_at = container_info.get('State', {}).get('StartedAt', '')
                        started_at_datetime = datetime.strptime(started_at[:26], "%Y-%m-%dT%H:%M:%S.%f")
                        uptime = datetime.now() - started_at_datetime

                        container_tree = tree.add(f"{container_name}")
                        container_tree.add(f"[bold cyan]Ports:[/bold cyan] {ports_str or 'N/A'}")
                        container_tree.add(f"[bold cyan]Image:[/bold cyan] {image}")
                        container_tree.add(f"[bold cyan]Uptime:[/bold cyan] {str(uptime).split('.')[0]}")  # Exclude microseconds for clarity

                else:
                    tree.add("[bold red]No containers found[/bold red]")

                console.print(tree)
            else:
                # Show overall deployment status
                result = subprocess.run(
                    ["docker", "compose", "-f", compose_file, "ps", "--quiet"],
                    capture_output=True, text=True)
                status = "Up" if result.stdout.strip() else "Down"

                # Create a simple tree for the overall status
                tree = Tree(f"[bold cyan]Deployment Status[/bold cyan]")
                status_style = "red" if status == "Down" else "green"
                tree.add(f"{name}: [{status_style}]{status}[/{status_style}]")

                console.print(tree)
        else:
            console.print(f"No docker-compose file found in {file_path}.", style="bold red")
    else:
        console.print(f"Deployment {name} not found.", style="bold red")

@click.command()
@click.option('--key', '-k', default=None, help='Retrieve a specific statistic by key.')
def statistics(key):
    """
    Display statistics about the deployments. Optionally retrieve a specific statistic by key.
    """
    deployments = load_deployments()
    num_deployments = len(deployments)

    # Calculate the number of Docker images used across all deployments
    images_used = 0
    for deployment in deployments.values():
        file_path = deployment.get('file_path')
        compose_file = get_compose_file_path(file_path)
        if compose_file:
            with open(compose_file, 'r') as file:
                compose_data = yaml.safe_load(file)
                services = compose_data.get('services', {})
                images_used += len(services)

    # Prepare data for the table
    stats_data = {
        "Deployments": num_deployments,
        "Images Used": images_used,
    }

    if key:
        # Display the specific key's value if it exists
        if key in stats_data:
            click.echo(stats_data[key])
        else:
            click.echo(f"Statistic with key '{key}' not found.")
    else:
        # Display all stats if no key is provided
        click.echo(tabulate(stats_data.items(), headers=["Key", "Value"], tablefmt="grid"))


