#!/usr/bin/env python3
"""
Main CLI entry point for Swarm Squad Ep2.

This module provides the command-line interface for managing the Swarm Squad
application including installation, launching services, and running components.
"""

import argparse
import sys
from typing import List, Optional

from swarm_squad_ep2.cli import (
    build_command,
    fastapi_command,
    install_command,
    launch_command,
    sim_command,
    webui_command,
)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the main argument parser."""
    parser = argparse.ArgumentParser(
        prog="swarm-squad-ep2",
        description="Swarm Squad Ep2: The Digital Dialogue - CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  swarm-squad-ep2 install                # Install frontend dependencies (dev only)
  swarm-squad-ep2 build                  # Build frontend for production (dev only)
  swarm-squad-ep2 launch                 # Launch both backend and frontend
  swarm-squad-ep2 sim                     # Run vehicle simulation
  swarm-squad-ep2 sim visualize          # Run matplotlib visualization
  swarm-squad-ep2 sim test               # Run WebSocket test client
  swarm-squad-ep2 fastapi --port 8080    # Run FastAPI on custom port
  swarm-squad-ep2 webui --port 3001      # Run frontend on custom port
        """,
    )

    # Add version flag
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.6",
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        title="commands",
        description="Choose a command to run",
    )

    # Install command
    install_parser = subparsers.add_parser(
        "install",
        help="Install frontend dependencies",
        description="Install frontend dependencies and setup the development environment",
    )
    install_parser.add_argument(
        "--force",
        action="store_true",
        help="Force reinstall dependencies even if they already exist",
    )
    install_parser.set_defaults(func=install_command)

    # Build command
    build_parser = subparsers.add_parser(
        "build",
        help="Build the frontend for production",
        description="Build the Next.js frontend for inclusion in the Python package",
    )
    build_parser.set_defaults(func=build_command)

    # Sim command with subcommands
    sim_parser = subparsers.add_parser(
        "sim",
        help="Run vehicle simulation components",
        description="Run vehicle simulation components",
    )

    # Create subparsers for sim subcommands
    sim_subparsers = sim_parser.add_subparsers(
        dest="sim_subcommand",
        help="Sim subcommands",
        title="sim subcommands",
        description="Choose what to run",
    )

    # Sim visualize subcommand
    sim_visualize_parser = sim_subparsers.add_parser(
        "visualize",
        help="Run the matplotlib visualization",
        description="Start the matplotlib-based vehicle visualization",
    )
    sim_visualize_parser.set_defaults(sim_subcommand="visualize")

    # Sim test subcommand
    sim_test_parser = sim_subparsers.add_parser(
        "test",
        help="Run the WebSocket test client",
        description="Start the WebSocket test client to monitor communication",
    )
    sim_test_parser.set_defaults(sim_subcommand="test")

    # Set default subcommand to 'run' if none specified (but no explicit run command)
    sim_parser.set_defaults(func=sim_command, sim_subcommand="run")

    # FastAPI command
    fastapi_parser = subparsers.add_parser(
        "fastapi",
        help="Run FastAPI backend server",
        description="Start the FastAPI backend server",
    )
    fastapi_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)",
    )
    fastapi_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)",
    )
    fastapi_parser.add_argument(
        "--reload",
        action="store_true",
        default=True,
        help="Enable auto-reload for development (default: True)",
    )
    fastapi_parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload",
    )
    fastapi_parser.set_defaults(func=fastapi_command)

    # WebUI command
    webui_parser = subparsers.add_parser(
        "webui",
        help="Run Next.js frontend server",
        description="Start the Next.js frontend development server",
    )
    webui_parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port to bind the frontend to (default: 3000)",
    )
    webui_parser.add_argument(
        "--host",
        default="localhost",
        help="Host to bind the frontend to (default: localhost)",
    )
    webui_parser.set_defaults(func=webui_command)

    # Launch command
    launch_parser = subparsers.add_parser(
        "launch",
        help="Launch both backend and frontend",
        description="Start both FastAPI backend and Next.js frontend simultaneously",
    )
    launch_parser.add_argument(
        "--backend-port",
        type=int,
        default=8000,
        help="Port for the backend server (default: 8000)",
    )
    launch_parser.add_argument(
        "--frontend-port",
        type=int,
        default=3000,
        help="Port for the frontend server (default: 3000)",
    )
    launch_parser.add_argument(
        "--backend-host",
        default="0.0.0.0",
        help="Host for the backend server (default: 0.0.0.0)",
    )
    launch_parser.add_argument(
        "--frontend-host",
        default="localhost",
        help="Host for the frontend server (default: localhost)",
    )
    launch_parser.set_defaults(func=launch_command)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args(argv)

    # If no command is provided, show help
    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    try:
        # Call the appropriate command function
        return args.func(args) or 0
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
