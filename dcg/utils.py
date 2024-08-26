#!/usr/bin/env python3
import os
import subprocess
import yaml
import requests

SETTINGS_FILE = os.path.expanduser("~/.dcg/settings.yaml")

def load_deployments():
    """Load deployments from the YAML settings file."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as file:
            data = yaml.safe_load(file)
            return data.get('deployments', [])
    return []

def save_deployments(deployments):
    """Save deployments to the YAML settings file."""
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w") as file:
        yaml.safe_dump({'deployments': deployments}, file, default_flow_style=False, sort_keys=False, indent=2)

def get_compose_file_path(file_path):
    """Return the path to the docker-compose file, checking for both yaml and yml extensions."""
    yaml_path = os.path.join(file_path, "docker-compose.yaml")
    yml_path = os.path.join(file_path, "docker-compose.yml")
    
    if os.path.exists(yaml_path):
        return yaml_path
    elif os.path.exists(yml_path):
        return yml_path
    else:
        return None

def manage_deployment(name, action):
    """
    Manage deployment with the given action.
    
    :param name: The name of the deployment.
    :param action: The action to perform (start, stop, restart).
    """
    deployments = load_deployments()

    for deployment in deployments:
        if name in deployment:
            file_path = deployment[name].get("file_path", "N/A")
            if action == "start":
                start_deployment(name, file_path)
            elif action == "stop":
                stop_deployment(name, file_path)
            elif action == "restart":
                stop_deployment(name, file_path)
                start_deployment(name, file_path)
            break
    else:
        click.echo(f"Deployment {name} not found.")

def start_deployment(name, file_path):
    """Helper function to start a deployment."""
    print(f"Attempting to start {name}...")
    compose_file = get_compose_file_path(file_path)
    if compose_file:
        subprocess.run(["docker", "compose", "-f", compose_file, "up", "-d"])
        print(f"Deployment {name} started.")
    else:
        print(f"No docker-compose file found in {file_path}.")

def stop_deployment(name, file_path):
    """Helper function to stop a deployment."""
    compose_file = get_compose_file_path(file_path)
    if compose_file:
        subprocess.run(["docker", "compose", "-f", compose_file, "down"])
        print(f"Deployment {name} stopped.")
    else:
        print(f"No docker-compose file found in {file_path}.")
