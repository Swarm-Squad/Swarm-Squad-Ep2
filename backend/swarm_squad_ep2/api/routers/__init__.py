"""
FastAPI routers for the Swarm Squad Ep2 application.

Contains routers for vehicles, LLMs, batch operations, real-time communication,
and vehicle-to-LLM mappings.
"""

from swarm_squad_ep2.api.routers import batch, llms, realtime, veh2llm, vehicles

__all__ = ["batch", "llms", "realtime", "veh2llm", "vehicles"]
