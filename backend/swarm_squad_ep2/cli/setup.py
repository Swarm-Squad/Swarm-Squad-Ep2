"""
Setup command for initializing and running the vehicle simulation.
"""

import subprocess
import sys
from typing import Any

from swarm_squad_ep2.cli.utils import (
    find_project_root,
    print_error,
    print_info,
    print_success,
)


def run_simulation(backend_dir) -> int:
    """Run the vehicle simulation."""
    script_path = backend_dir / "swarm_squad_ep2" / "scripts" / "run_simulation.py"

    if not script_path.exists():
        print_error(f"Simulation script not found: {script_path}")
        return 1

    print_info("Initializing vehicle simulation with 3 vehicles...")
    print_info("This will create real-time vehicle data for the frontend.")
    print_info("Press Ctrl+C to stop the simulation.")
    print_info("")

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=backend_dir,
            check=False,
        )

        if result.returncode == 0:
            print_success("Simulation completed successfully!")
        elif result.returncode == 130:
            print_info("Simulation stopped by user.")
        else:
            print_error(f"Simulation exited with code {result.returncode}")

        return result.returncode

    except KeyboardInterrupt:
        print_info("\nSimulation stopped by user.")
        return 0
    except Exception as e:
        print_error(f"Failed to run simulation: {e}")
        return 1


def run_visualization(backend_dir) -> int:
    """Run the vehicle visualization."""
    script_path = (
        backend_dir / "swarm_squad_ep2" / "scripts" / "visualize_simulation.py"
    )

    if not script_path.exists():
        print_error(f"Visualization script not found: {script_path}")
        return 1

    print_info("Opening vehicle visualization window...")
    print_info("Make sure the FastAPI server and simulation are running first:")
    print_info("  1. swarm-squad-ep2 fastapi")
    print_info("  2. swarm-squad-ep2 setup")
    print_info("")
    print_info("Close the matplotlib window to stop the visualization.")
    print_info("")

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=backend_dir,
            check=False,
        )

        if result.returncode == 0:
            print_success("Visualization completed successfully!")
        elif result.returncode == 130:
            print_info("Visualization stopped by user.")
        else:
            print_error(f"Visualization exited with code {result.returncode}")

        return result.returncode

    except KeyboardInterrupt:
        print_info("\nVisualization stopped by user.")
        return 0
    except Exception as e:
        print_error(f"Failed to run visualization: {e}")
        return 1


def run_test_client(backend_dir) -> int:
    """Run the test client."""
    script_path = backend_dir / "swarm_squad_ep2" / "scripts" / "test_client.py"

    if not script_path.exists():
        print_error(f"Test client script not found: {script_path}")
        return 1

    print_info("Starting WebSocket test client...")
    print_info("This will monitor Vehicle 1's communication rooms:")
    print_info("  - V2V Room (v1): Vehicle-to-Vehicle communication")
    print_info("  - V2L Room (vl1): Vehicle-to-LLM communication")
    print_info("  - L2L Room (l1): LLM-to-LLM communication")
    print_info("")
    print_info("Press Ctrl+C to stop the test client.")
    print_info("")

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=backend_dir,
            check=False,
        )

        if result.returncode == 0:
            print_success("Test client completed successfully!")
        elif result.returncode == 130:
            print_info("Test client stopped by user.")
        else:
            print_error(f"Test client exited with code {result.returncode}")

        return result.returncode

    except KeyboardInterrupt:
        print_info("\nTest client stopped by user.")
        return 0
    except Exception as e:
        print_error(f"Failed to run test client: {e}")
        return 1


def setup_command(args: Any) -> int:
    """
    Setup and run vehicle simulation components.

    Subcommands:
        run (default): Run the vehicle simulation
        visualize: Run the matplotlib visualization
        test: Run the WebSocket test client

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Find project root
    project_root = find_project_root()
    if not project_root:
        print_error("Could not find project root directory")
        return 1

    backend_dir = project_root / "backend"

    # Get the subcommand (default to 'run' if none specified)
    subcommand = getattr(args, "setup_subcommand", "run")

    if subcommand == "run":
        print_info("Starting vehicle simulation...")
        return run_simulation(backend_dir)
    elif subcommand == "visualize":
        print_info("Starting vehicle simulation visualization...")
        return run_visualization(backend_dir)
    elif subcommand == "test":
        print_info("Starting WebSocket test client...")
        return run_test_client(backend_dir)
    else:
        print_error(f"Unknown subcommand: {subcommand}")
        print_info("Available subcommands: run, visualize, test")
        return 1
