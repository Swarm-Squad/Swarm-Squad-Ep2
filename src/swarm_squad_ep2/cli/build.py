"""
Build command for building the Next.js frontend.
"""

import shutil
import subprocess
from pathlib import Path
from typing import Any

from swarm_squad_ep2.cli.utils import (
    find_project_root,
    print_error,
    print_info,
    print_success,
)


def run_command(cmd, cwd=None):
    """Run a command and handle errors."""
    print_info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, cwd=cwd, check=True, capture_output=True, text=True
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False


def build_frontend(project_root: Path) -> bool:
    """Build the Next.js frontend."""
    print_info("Building Next.js frontend...")

    web_dir = project_root / "src" / "swarm_squad_ep2" / "web"

    if not web_dir.exists():
        print_error(f"Web directory not found at {web_dir}")
        print_info("Make sure you're running this from the project root directory.")
        return False

    # Check if pnpm is available
    if not shutil.which("pnpm"):
        print_error("pnpm is not installed. Please install pnpm first.")
        print_info("Install with: npm install -g pnpm")
        return False

    # Install dependencies
    print_info("Installing frontend dependencies...")
    if not run_command(["pnpm", "install"], cwd=web_dir):
        return False

    # Build the frontend
    print_info("Building frontend for production...")
    if not run_command(["pnpm", "build"], cwd=web_dir):
        return False

    print_success("Frontend build completed successfully!")
    return True


def verify_build_output(project_root: Path) -> bool:
    """Verify that the build output exists."""
    web_dir = project_root / "src" / "swarm_squad_ep2" / "web"
    out_dir = web_dir / "out"

    if not out_dir.exists():
        print_error("Build output directory 'src/swarm_squad_ep2/web/out' not found.")
        print_info(
            "The Next.js build may have failed or used a different output directory."
        )
        return False

    # Check if there are files in the output directory
    files = list(out_dir.rglob("*"))
    if not files:
        print_error("Build output directory is empty.")
        return False

    print_success(f"Build output verified: {len(files)} files in {out_dir}")
    return True


def build_command(args: Any) -> int:
    """
    Build the Next.js frontend for inclusion in the Python package.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print_info("Starting frontend build process...")

    # Find project root (must be in development mode for building)
    project_root = find_project_root()
    if not project_root:
        print_error("Could not find project root directory")
        print_info(
            "Make sure you're running this from the project directory containing pyproject.toml"
        )
        return 1

    # Verify we're in development mode (has pyproject.toml)
    if not (project_root / "pyproject.toml").exists():
        print_error("This command must be run from the development environment")
        print_info("This command requires the source repository with pyproject.toml")
        return 1

    try:
        # Build the frontend
        if not build_frontend(project_root):
            print_error("Failed to build frontend")
            return 1

        # Verify build output
        if not verify_build_output(project_root):
            print_error("Build verification failed")
            return 1

        print_success("Frontend build process completed successfully!")
        print_info(
            "The built frontend is now ready to be included in the Python package."
        )
        print_info("Run 'uv build' to create a wheel with the built frontend included.")

        return 0

    except KeyboardInterrupt:
        print_info("\nBuild process cancelled by user")
        return 0
    except Exception as e:
        print_error(f"Unexpected error during build: {e}")
        return 1
