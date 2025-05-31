"""
Launch command for running both backend and frontend simultaneously.
"""

import signal
import subprocess
import sys
import threading
import time
from typing import Any, List, Optional

from swarm_squad_ep2.cli.utils import (
    check_frontend_dependencies_installed,
    find_project_root,
    get_free_port,
    get_frontend_directory,
    is_development_mode,
    is_port_in_use,
    kill_processes_on_port,
    print_error,
    print_info,
    print_success,
    print_warning,
)


class ProcessManager:
    """Manage multiple processes and handle graceful shutdown."""

    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.shutdown_event = threading.Event()

    def add_process(self, process: subprocess.Popen) -> None:
        """Add a process to be managed."""
        self.processes.append(process)

    def shutdown_all(self) -> None:
        """Shutdown all managed processes."""
        self.shutdown_event.set()

        for process in self.processes:
            if process.poll() is None:  # Process is still running
                print_info(f"Stopping process {process.pid}...")
                try:
                    # Try graceful termination first
                    process.terminate()
                    # Wait for process to terminate gracefully
                    process.wait(timeout=3)
                    print_info(f"Process {process.pid} stopped gracefully")
                except subprocess.TimeoutExpired:
                    print_warning(f"Force killing process {process.pid}")
                    process.kill()
                    try:
                        process.wait(timeout=2)
                        print_info(f"Process {process.pid} force killed")
                    except subprocess.TimeoutExpired:
                        print_error(f"Failed to kill process {process.pid}")
                except Exception as e:
                    print_error(f"Error stopping process {process.pid}: {e}")
                    # Try force kill as last resort
                    try:
                        process.kill()
                        process.wait(timeout=1)
                    except Exception:
                        pass

        self.processes.clear()

    def wait_for_processes(self) -> int:
        """Wait for all processes to complete or shutdown event."""
        try:
            while not self.shutdown_event.is_set():
                # Check if any process has exited
                for process in self.processes:
                    if process.poll() is not None:
                        # Process has exited
                        if process.returncode != 0:
                            print_error(
                                f"Process {process.pid} exited with code {process.returncode}"
                            )
                            return process.returncode
                        else:
                            print_info(f"Process {process.pid} completed successfully")

                time.sleep(0.5)

            return 0

        except KeyboardInterrupt:
            print_info("\nShutdown requested by user")
            return 0


def start_backend(
    args: Any, process_manager: ProcessManager, dev_mode: bool
) -> Optional[subprocess.Popen]:
    """Start the FastAPI backend server."""
    project_root = find_project_root()
    if not project_root:
        return None

    # Check if port is in use
    if is_port_in_use(args.backend_port, args.backend_host):
        print_warning(f"Backend port {args.backend_port} is already in use")
        free_port = get_free_port(args.backend_port + 1)
        if free_port:
            print_info(f"Using backend port {free_port} instead")
            args.backend_port = free_port
        else:
            print_error("Could not find a free port for backend")
            return None

    print_info(f"Starting backend server on {args.backend_host}:{args.backend_port}")
    print_info(f"Mode: {'Development' if dev_mode else 'Installed'}")

    try:
        # Determine the correct working directory and environment
        if dev_mode:
            # Development mode: use src directory
            src_dir = project_root / "src"
            cwd = src_dir
            env = {
                "PYTHONPATH": str(src_dir),
                **dict(subprocess.os.environ),
            }
        else:
            # Installed mode: use project root
            cwd = project_root
            env = dict(subprocess.os.environ)

        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "swarm_squad_ep2.api.main:app",
                "--host",
                args.backend_host,
                "--port",
                str(args.backend_port),
                "--reload",
            ],
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        process_manager.add_process(process)
        return process

    except Exception as e:
        print_error(f"Failed to start backend: {e}")
        return None


def start_frontend(
    args: Any, process_manager: ProcessManager, dev_mode: bool
) -> Optional[subprocess.Popen]:
    """Start the frontend server (Next.js dev server or static file server)."""
    project_root = find_project_root()
    if not project_root:
        return None

    # Get frontend directory based on mode
    frontend_dir = get_frontend_directory(project_root)
    if not frontend_dir:
        if dev_mode:
            print_error(
                "Frontend directory not found. Make sure you're in the project root."
            )
        else:
            print_error("Built frontend not found in installed package.")
        return None

    # Check frontend dependencies in development mode
    if dev_mode and not check_frontend_dependencies_installed(frontend_dir):
        print_error("Frontend dependencies not installed.")
        print_info("Run 'swarm-squad-ep2 install' to install dependencies first.")
        return None

    # Check if port is in use and find free port
    original_port = args.frontend_port
    if is_port_in_use(args.frontend_port, args.frontend_host):
        print_warning(f"Frontend port {args.frontend_port} is already in use")
        free_port = get_free_port(args.frontend_port + 1)
        if free_port:
            print_info(f"Using frontend port {free_port} instead")
            args.frontend_port = free_port
        else:
            print_error("Could not find a free port for frontend")
            return None

    print_info(f"Starting frontend server on {args.frontend_host}:{args.frontend_port}")
    print_info(f"Mode: {'Development' if dev_mode else 'Installed'}")

    try:
        if dev_mode:
            # Development mode: Next.js dev server
            # Kill any existing processes on the port first
            if args.frontend_port != original_port:
                kill_processes_on_port(original_port)

            env = {
                "PORT": str(args.frontend_port),
                "HOSTNAME": args.frontend_host,
                **dict(subprocess.os.environ),
            }

            process = subprocess.Popen(
                ["pnpm", "dev"],
                cwd=frontend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            # Wait a moment and check if the process started successfully
            time.sleep(2)
            if process.poll() is not None:
                print_error("Next.js dev server failed to start")
                if process.stdout:
                    output = process.stdout.read()
                    if output:
                        print_error(f"Next.js output: {output}")
                return None
        else:
            # Installed mode: static file server from out directory
            # Create a custom server script for serving Next.js static export
            server_script = f'''
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
    with socketserver.TCPServer(("{args.frontend_host}", {args.frontend_port}), NextJSHandler) as httpd:
        print(f"Serving Next.js static files at http://{args.frontend_host}:{args.frontend_port}")
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\\nServer stopped by user")
except Exception as e:
    print(f"Server error: {{e}}")
'''

            process = subprocess.Popen(
                [sys.executable, "-c", server_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            # Wait a moment and check if the process started successfully
            time.sleep(1)
            if process.poll() is not None:
                print_error("Static file server failed to start")
                return None
        process_manager.add_process(process)
        return process

    except Exception as e:
        print_error(f"Failed to start frontend: {e}")
        return None


def stream_output(process: subprocess.Popen, prefix: str) -> None:
    """Stream output from a process with a prefix."""
    if process.stdout:
        for line in iter(process.stdout.readline, ""):
            if line:
                print(f"[{prefix}] {line.strip()}")
            if process.poll() is not None:
                break


def launch_command(args: Any) -> int:
    """
    Launch both FastAPI backend and Next.js frontend simultaneously.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print_info("Launching Swarm Squad Ep2 application...")

    # Check mode once and cache the result
    dev_mode = is_development_mode()

    process_manager = ProcessManager()

    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print_info(f"\nReceived signal {signum}, shutting down...")
        process_manager.shutdown_all()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start backend
        backend_process = start_backend(args, process_manager, dev_mode)
        if not backend_process:
            return 1

        # Wait a moment for backend to start
        time.sleep(2)

        # Start frontend
        frontend_process = start_frontend(args, process_manager, dev_mode)
        if not frontend_process:
            process_manager.shutdown_all()
            return 1

        # Start output streaming threads
        backend_thread = threading.Thread(
            target=stream_output, args=(backend_process, "BACKEND"), daemon=True
        )
        frontend_thread = threading.Thread(
            target=stream_output, args=(frontend_process, "FRONTEND"), daemon=True
        )

        backend_thread.start()
        frontend_thread.start()

        print_success("Both servers started successfully!")
        print_info(f"Backend:  http://{args.backend_host}:{args.backend_port}")
        print_info(f"Frontend: http://{args.frontend_host}:{args.frontend_port}")
        print_info("Press Ctrl+C to stop both servers")

        # Wait for processes to complete
        return process_manager.wait_for_processes()

    except Exception as e:
        print_error(f"Failed to launch application: {e}")
        return 1
    finally:
        process_manager.shutdown_all()
