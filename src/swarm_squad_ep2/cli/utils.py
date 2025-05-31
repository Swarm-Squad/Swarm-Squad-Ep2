"""
Utility functions for CLI commands.
"""

import socket
import subprocess
import sys
from pathlib import Path
from typing import Optional


# ANSI color codes for terminal output
class Colors:
    """ANSI color codes for terminal output."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"


def print_info(message: str) -> None:
    """Print an info message in blue."""
    print(f"{Colors.BLUE}INFO: {message}{Colors.RESET}")


def print_success(message: str) -> None:
    """Print a success message in green."""
    print(f"{Colors.GREEN}SUCCESS: {message}{Colors.RESET}")


def print_error(message: str) -> None:
    """Print an error message in red."""
    print(f"{Colors.RED}ERROR: {message}{Colors.RESET}", file=sys.stderr)


def print_warning(message: str) -> None:
    """Print a warning message in yellow."""
    print(f"{Colors.YELLOW}WARNING: {message}{Colors.RESET}")


def find_project_root() -> Optional[Path]:
    """
    Find the project root directory.

    In development mode: looks for pyproject.toml
    In installed mode: uses the package installation directory

    Returns:
        Path to project root or None if not found
    """
    # Development mode: look for pyproject.toml first
    current = Path.cwd()

    # First check current directory
    if (current / "pyproject.toml").exists():
        print_info(f"Running in development mode from: {current}")
        return current

    # Then check parent directories
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            print_info(f"Running in development mode from: {parent}")
            return parent

    # Check if we're already in the backend directory
    backend_main = Path(__file__).parent.parent.parent.parent
    if (backend_main / "pyproject.toml").exists():
        print_info(f"Running in development mode from: {backend_main}")
        return backend_main

    # If no pyproject.toml found, try to detect if we're running from an installed package
    try:
        import swarm_squad_ep2

        package_dir = Path(swarm_squad_ep2.__file__).parent

        # Check if this looks like an installed package
        # (has the expected structure but no pyproject.toml)
        if (package_dir / "api").exists() and (package_dir / "cli").exists():
            print_info(f"Running in installed mode from: {package_dir.parent}")
            return package_dir.parent
    except ImportError:
        pass

    return None


def check_frontend_dependencies_installed(frontend_dir: Path) -> bool:
    """
    Check if frontend dependencies are installed.

    Args:
        frontend_dir: Path to frontend directory

    Returns:
        True if dependencies are installed, False otherwise
    """
    node_modules = frontend_dir / "node_modules"
    package_lock = frontend_dir / "pnpm-lock.yaml"

    return node_modules.exists() and package_lock.exists()


def get_free_port(start_port: int = 8000, max_attempts: int = 100) -> Optional[int]:
    """
    Find a free port starting from the given port.

    Args:
        start_port: Port to start checking from
        max_attempts: Maximum number of ports to check

    Returns:
        Free port number or None if no free port found
    """

    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("localhost", port))
                return port
            except socket.error:
                continue

    return None


def is_port_in_use(port: int, host: str = "localhost") -> bool:
    """
    Check if a port is in use.

    Args:
        port: Port number to check
        host: Host to check on

    Returns:
        True if port is in use, False otherwise
    """

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
            return False
        except socket.error:
            return True


def kill_processes_on_port(port: int, host: str = "localhost") -> bool:
    """
    Kill any processes using the specified port.

    Args:
        port: Port number to check
        host: Host to check (default: localhost)

    Returns:
        True if any processes were killed, False otherwise
    """
    try:
        if sys.platform == "win32":
            # Windows
            result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split("\n")
                for line in lines:
                    if f":{port}" in line and "LISTENING" in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            try:
                                subprocess.run(
                                    ["taskkill", "/PID", pid, "/F"], capture_output=True
                                )
                                print_info(f"Killed process {pid} using port {port}")
                                return True
                            except Exception:
                                pass
        else:
            # Unix-like systems (Linux, macOS)
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"], capture_output=True, text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split("\n")
                for pid in pids:
                    if pid:
                        try:
                            subprocess.run(["kill", "-9", pid], capture_output=True)
                            print_info(f"Killed process {pid} using port {port}")
                            return True
                        except Exception:
                            pass
    except Exception as e:
        print_warning(f"Could not check/kill processes on port {port}: {e}")

    return False


def is_development_mode() -> bool:
    """
    Check if we're running in development mode.

    Returns:
        True if in development mode, False if installed
    """
    project_root = find_project_root()
    if project_root:
        return (project_root / "pyproject.toml").exists()
    return False


def get_frontend_directory(project_root: Path) -> Optional[Path]:
    """
    Get the frontend directory based on the mode.

    Args:
        project_root: The project root directory

    Returns:
        Path to frontend directory or None if not found
    """
    if is_development_mode():
        # Development mode: use source web directory
        web_dir = project_root / "src" / "swarm_squad_ep2" / "web"
        if web_dir.exists():
            return web_dir
    else:
        # Installed mode: look for bundled web directory
        package_dir = project_root / "swarm_squad_ep2"
        web_dir = package_dir / "web" / "out"
        if web_dir.exists():
            return web_dir

        # Fallback: check if static frontend exists in package
        static_dir = package_dir / "static" / "frontend"
        if static_dir.exists():
            return static_dir

    return None
