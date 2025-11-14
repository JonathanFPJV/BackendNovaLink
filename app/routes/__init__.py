"""
Routers de la API
"""
from .auth import router as auth_router
from .cursos import router as cursos_router
from .lecciones import router as lecciones_router
from .examenes import router as examenes_router

__all__ = ["auth_router", "cursos_router", "lecciones_router", "examenes_router"]
