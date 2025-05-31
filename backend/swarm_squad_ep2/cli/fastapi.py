"""
FastAPI command for running the backend server.
"""

import signal
import subprocess
import sys
from typing import Any, Optional

from swarm_squad_ep2.cli.utils import (
    find_project_root,
    get_free_port,
    is_port_in_use,
    print_error,
    print_info,
    print_success,
    print_warning,
)


class FastAPIProcessManager:
    """Manage FastAPI process and handle graceful shutdown."""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None

    def start_process(self, host: str, port: int, reload: bool, backend_dir) -> bool:
        """Start the FastAPI process."""
        try:
            # Add backend directory to Python path
            env = {
                "PYTHONPATH": str(backend_dir),
                **dict(subprocess.os.environ),
            }

            self.process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "swarm_squad_ep2.api.main:app",
                    "--host",
                    host,
                    "--port",
                    str(port),
                ]
                + (["--reload"] if reload else []),
                cwd=backend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            return True

        except Exception as e:
            print_error(f"Failed to start FastAPI server: {e}")
            return False

    def shutdown(self) -> None:
        """Shutdown the FastAPI process."""
        if self.process and self.process.poll() is None:
            print_info("Stopping FastAPI server...")
            try:
                self.process.terminate()
                # Wait for process to terminate gracefully
                self.process.wait(timeout=5)
                print_info("FastAPI server stopped successfully")
            except subprocess.TimeoutExpired:
                print_warning("Force killing FastAPI server")
                self.process.kill()
                self.process.wait()
            except Exception as e:
                print_error(f"Error stopping FastAPI server: {e}")
            finally:
                self.process = None

    def wait(self) -> int:
        """Wait for the process to complete."""
        if self.process:
            return self.process.wait()
        return 0


def fastapi_command(args: Any) -> int:
    """
    Run the FastAPI backend server.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print_info("Starting FastAPI backend server...")

    # Find project root
    project_root = find_project_root()
    if not project_root:
        print_error("Could not find project root directory")
        return 1

    # Configure server parameters
    host = args.host
    port = args.port
    reload = args.reload and not args.no_reload

    # Check if port is in use
    if is_port_in_use(port, host):
        print_warning(f"Port {port} is already in use on {host}")

        # Try to find a free port
        free_port = get_free_port(port + 1)
        if free_port:
            print_info(f"Using port {free_port} instead")
            port = free_port
        else:
            print_error("Could not find a free port")
            return 1

    # Set up the module path for the FastAPI app
    backend_dir = project_root / "backend"
    api_dir = backend_dir / "swarm_squad_ep2" / "api"

    if not api_dir.exists():
        print_error(f"API directory not found: {api_dir}")
        return 1

    print_info("Server configuration:")
    print_info(f"  Host: {host}")
    print_info(f"  Port: {port}")
    print_info(f"  Reload: {reload}")
    print_info(f"  API Directory: {api_dir}")

    # Create process manager
    process_manager = FastAPIProcessManager()

    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print_info(f"\nReceived signal {signum}, shutting down FastAPI server...")
        process_manager.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start the FastAPI server
        print_success(f"FastAPI server starting on http://{host}:{port}")
        print_info("Press Ctrl+C to stop the server")

        if not process_manager.start_process(host, port, reload, backend_dir):
            return 1

        # Stream output from the process
        if process_manager.process and process_manager.process.stdout:
            try:
                for line in iter(process_manager.process.stdout.readline, ""):
                    if line:
                        print(f"[FASTAPI] {line.strip()}")
                    if process_manager.process.poll() is not None:
                        break
            except KeyboardInterrupt:
                pass

        return process_manager.wait()

    except KeyboardInterrupt:
        print_info("\nServer stopped by user")
        return 0
    except Exception as e:
        print_error(f"Failed to start server: {e}")
        return 1
    finally:
        process_manager.shutdown()
