"""
Install command for setting up frontend dependencies.
"""

import subprocess
from pathlib import Path
from typing import Any

from swarm_squad_ep2.cli.utils import (
    find_project_root,
    print_error,
    print_info,
    print_success,
)


def check_pnpm_installed() -> bool:
    """Check if pnpm is installed on the system."""
    try:
        result = subprocess.run(
            ["pnpm", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        print_info(f"Found pnpm version: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_pnpm() -> bool:
    """Install pnpm globally using npm."""
    print_info("Installing pnpm...")
    try:
        subprocess.run(
            ["npm", "install", "-g", "pnpm"],
            check=True,
        )
        print_success("pnpm installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install pnpm: {e}")
        return False
    except FileNotFoundError:
        print_error("npm not found. Please install Node.js and npm first.")
        return False


def check_node_installed() -> bool:
    """Check if Node.js is installed."""
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        print_info(f"Found Node.js version: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_frontend_dependencies(frontend_dir: Path, force: bool = False) -> bool:
    """Install frontend dependencies using pnpm."""
    if not frontend_dir.exists():
        print_error(f"Frontend directory not found: {frontend_dir}")
        print_info(
            "The install command is only available when running from the source repository"
        )
        return False

    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        print_error(f"package.json not found in {frontend_dir}")
        return False

    # Check if dependencies are already installed
    node_modules = frontend_dir / "node_modules"
    if node_modules.exists() and not force:
        print_info("Frontend dependencies already installed. Use --force to reinstall.")
        return True

    print_info("Installing frontend dependencies...")
    try:
        # Change to frontend directory and run pnpm install
        subprocess.run(
            ["pnpm", "install"],
            cwd=frontend_dir,
            check=True,
        )
        print_success("Frontend dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install frontend dependencies: {e}")
        return False


def install_command(args: Any) -> int:
    """
    Install frontend dependencies and setup development environment.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print_info("Starting installation process...")

    # Find project root
    project_root = find_project_root()
    if not project_root:
        print_error("Could not find project root directory")
        return 1

    # Check if we're in development mode
    if not (project_root / "pyproject.toml").exists():
        print_error("Install command is only available in development mode")
        print_info("This command requires the source repository with pyproject.toml")
        return 1

    web_dir = project_root / "src" / "swarm_squad_ep2" / "web"

    if not web_dir.exists():
        print_error(f"Web directory not found: {web_dir}")
        print_info(
            "The install command is only available when running from the source repository"
        )
        return 1

    # Check if Node.js is installed
    if not check_node_installed():
        print_error("Node.js is not installed. Please install Node.js first.")
        print_info("Visit: https://nodejs.org/")
        return 1

    # Check if pnpm is installed, install if not
    if not check_pnpm_installed():
        print_info("pnpm not found. Installing pnpm...")
        if not install_pnpm():
            print_error("Failed to install pnpm. Please install it manually:")
            print_info("npm install -g pnpm")
            return 1

    # Install frontend dependencies
    if not install_frontend_dependencies(web_dir, force=args.force):
        return 1

    print_success("Installation completed successfully!")
    print_info("You can now run 'swarm-squad-ep2 launch' to start the application.")

    return 0
