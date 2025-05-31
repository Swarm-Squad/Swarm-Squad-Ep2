"""
CLI commands for Swarm Squad Ep2.
"""

from swarm_squad_ep2.cli.build import build_command
from swarm_squad_ep2.cli.fastapi import fastapi_command
from swarm_squad_ep2.cli.install import install_command
from swarm_squad_ep2.cli.launch import launch_command
from swarm_squad_ep2.cli.setup import setup_command
from swarm_squad_ep2.cli.webui import webui_command

__all__ = [
    "build_command",
    "install_command",
    "fastapi_command",
    "webui_command",
    "launch_command",
    "setup_command",
]
