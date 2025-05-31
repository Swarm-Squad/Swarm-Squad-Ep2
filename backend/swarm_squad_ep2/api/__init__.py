"""
API package for Swarm Squad Ep2.

Contains FastAPI application, database connections, models, and routers.
"""

from swarm_squad_ep2.api import models
from swarm_squad_ep2.api.main import app

__all__ = ["app", "models"]
