#!/usr/bin/env python3
import click
from .commands import add, remove, update, up, down, restart, list_deployments, status, stop_all, start_all, statistics

@click.group()
def cli():
    pass

cli.add_command(add)
cli.add_command(remove)
cli.add_command(update)
cli.add_command(up)
cli.add_command(up, name="start")
cli.add_command(down)
cli.add_command(down, name="stop")
cli.add_command(restart)
cli.add_command(list_deployments, name="list")
cli.add_command(status)
cli.add_command(stop_all)
cli.add_command(start_all)
cli.add_command(statistics)
cli.add_command(statistics, name="stats")

if __name__ == "__main__":
    cli(prog_name="dcg")
