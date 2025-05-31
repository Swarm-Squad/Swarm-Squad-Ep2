"""
WebUI command for running the Next.js frontend.
"""

import signal
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

from swarm_squad_ep2.cli.utils import (
    check_frontend_dependencies_installed,
    find_project_root,
    get_free_port,
    get_frontend_directory,
    is_development_mode,
    is_port_in_use,
    print_error,
    print_info,
    print_success,
    print_warning,
)


class WebUIProcessManager:
    """Manage Next.js process and handle graceful shutdown."""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None

    def start_process(self, host: str, port: int, frontend_dir: Path) -> bool:
        """Start the Next.js process."""
        try:
            # Set environment variables for Next.js
            env = {
                "PORT": str(port),
                "HOSTNAME": host,
                **dict(subprocess.os.environ),
            }

            self.process = subprocess.Popen(
                ["pnpm", "dev"],
                cwd=frontend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            return True

        except FileNotFoundError:
            print_error("pnpm not found. Please run 'swarm-squad-ep2 install' first.")
            return False
        except Exception as e:
            print_error(f"Failed to start Next.js server: {e}")
            return False

    def shutdown(self) -> None:
        """Shutdown the Next.js process."""
        if self.process and self.process.poll() is None:
            print_info("Stopping Next.js server...")
            try:
                self.process.terminate()
                # Wait for process to terminate gracefully
                self.process.wait(timeout=5)
                print_info("Next.js server stopped successfully")
            except subprocess.TimeoutExpired:
                print_warning("Force killing Next.js server")
                self.process.kill()
                self.process.wait()
            except Exception as e:
                print_error(f"Error stopping Next.js server: {e}")
            finally:
                self.process = None

    def wait(self) -> int:
        """Wait for the process to complete."""
        if self.process:
            return self.process.wait()
        return 0


class StaticFileServer:
    """Static file server for serving built Next.js frontend."""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None

    def start_server(self, frontend_dir: Path, host: str, port: int) -> bool:
        """Start a static file server for Next.js export."""
        try:
            # Create a custom server script for serving Next.js static export
            server_script = self._create_server_script(frontend_dir, host, port)

            self.process = subprocess.Popen(
                [sys.executable, "-c", server_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            return True

        except Exception as e:
            print_error(f"Failed to start static file server: {e}")
            return False

    def _create_server_script(self, frontend_dir: Path, host: str, port: int) -> str:
        """Create a Python script for serving Next.js static files."""
        return f'''
import http.server
import socketserver
import os
from pathlib import Path

class NextJSHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="{frontend_dir}", **kwargs)
    
    def do_GET(self):
        # Handle root path
        if self.path == "/" or self.path == "":
            self.path = "/index.html"
        
        # Handle paths without extensions (SPA routing)
        if "." not in self.path.split("/")[-1] and not self.path.endswith("/"):
            # Check if the file exists as-is
            file_path = Path("{frontend_dir}") / self.path.lstrip("/")
            if not file_path.exists():
                # Try with .html extension
                html_path = file_path.with_suffix(".html")
                if html_path.exists():
                    self.path = "/" + str(html_path.relative_to(Path("{frontend_dir}")))
                else:
                    # Fallback to index.html for SPA routing
                    self.path = "/index.html"
        
        return super().do_GET()
    
    def end_headers(self):
        # Add CORS headers for development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

try:
    with socketserver.TCPServer(("{host}", {port}), NextJSHandler) as httpd:
        print(f"Serving Next.js static files at http://{host}:{port}")
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\\nServer stopped by user")
except Exception as e:
    print(f"Server error: {{e}}")
'''

    def shutdown(self) -> None:
        """Shutdown the static file server."""
        if self.process and self.process.poll() is None:
            print_info("Stopping static file server...")
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                print_info("Static file server stopped successfully")
            except subprocess.TimeoutExpired:
                print_warning("Force killing static file server")
                self.process.kill()
                self.process.wait()
            except Exception as e:
                print_error(f"Error stopping static file server: {e}")
            finally:
                self.process = None

    def wait(self) -> int:
        """Wait for the process to complete."""
        if self.process:
            return self.process.wait()
        return 0


def check_frontend_ready(frontend_dir: Path) -> bool:
    """
    Check if the frontend is ready to run.

    Args:
        frontend_dir: Path to frontend directory

    Returns:
        True if ready, False otherwise
    """
    if not frontend_dir.exists():
        print_error(f"Frontend directory not found: {frontend_dir}")
        return False

    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        print_error(f"package.json not found in {frontend_dir}")
        return False

    if not check_frontend_dependencies_installed(frontend_dir):
        print_error("Frontend dependencies not installed.")
        print_info("Run 'swarm-squad-ep2 install' to install dependencies first.")
        return False

    return True


def webui_command(args: Any) -> int:
    """
    Run the frontend server (Next.js dev server or static file server).

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print_info("Starting frontend server...")

    # Find project root
    project_root = find_project_root()
    if not project_root:
        print_error("Could not find project root directory")
        return 1

    # Check mode once and cache the result
    dev_mode = is_development_mode()

    # Get frontend directory based on mode
    frontend_dir = get_frontend_directory(project_root)
    if not frontend_dir:
        if dev_mode:
            print_error(
                "Frontend directory not found. Make sure you're in the project root."
            )
            print_info("Expected structure: project_root/frontend/")
        else:
            print_error("Built frontend not found in installed package.")
            print_info("The package may not include the frontend build files.")
        return 1

    # Configure server parameters
    host = args.host
    port = args.port

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

    print_info("Frontend configuration:")
    print_info(f"  Mode: {'Development' if dev_mode else 'Installed'}")
    print_info(f"  Host: {host}")
    print_info(f"  Port: {port}")
    print_info(f"  Frontend Directory: {frontend_dir}")

    # Choose the appropriate server based on mode
    if dev_mode:
        # Development mode: use Next.js dev server
        if not check_frontend_ready(frontend_dir):
            return 1

        process_manager = WebUIProcessManager()
    else:
        # Installed mode: use static file server
        process_manager = StaticFileServer()

    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print_info(f"\nReceived signal {signum}, shutting down frontend server...")
        process_manager.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start the appropriate server
        if dev_mode:
            print_success(
                f"Next.js development server starting on http://{host}:{port}"
            )
            print_info("Press Ctrl+C to stop the server")

            if not process_manager.start_process(host, port, frontend_dir):
                return 1
        else:
            print_success(f"Static file server starting on http://{host}:{port}")
            print_info("Press Ctrl+C to stop the server")

            if not process_manager.start_server(frontend_dir, host, port):
                return 1

        # Stream output from the process
        if (
            hasattr(process_manager, "process")
            and process_manager.process
            and process_manager.process.stdout
        ):
            try:
                prefix = "NEXT.JS" if dev_mode else "STATIC"
                for line in iter(process_manager.process.stdout.readline, ""):
                    if line:
                        print(f"[{prefix}] {line.strip()}")
                    if process_manager.process.poll() is not None:
                        break
            except KeyboardInterrupt:
                pass

        return process_manager.wait()

    except KeyboardInterrupt:
        print_info("\nFrontend server stopped by user")
        return 0
    except Exception as e:
        print_error(f"Failed to start frontend server: {e}")
        return 1
    finally:
        process_manager.shutdown()
