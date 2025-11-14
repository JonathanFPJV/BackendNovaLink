"""
NovaLinq API - Plataforma educativa con IA
Arquitectura limpia con separación de responsabilidades
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.utils.database import engine, Base
from app.routes import auth_router, cursos_router, lecciones_router, examenes_router

# Crear las tablas en la BD al iniciar
Base.metadata.create_all(bind=engine)

# Crear aplicación FastAPI
app = FastAPI(
    title="NovaLinq API",
    description="Plataforma educativa multiplataforma con IA generativa",
    version="2.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(auth_router)
app.include_router(cursos_router)
app.include_router(lecciones_router)
app.include_router(examenes_router)

@app.get("/")
def root():
    """Endpoint raíz de la API"""
    return {
        "mensaje": "NovaLinq API - Arquitectura Limpia",
        "version": "2.0.0",
        "docs": "/docs",
        "status": "running"
    }

@app.get("/health")
def health_check():
    """Verificar estado de la API"""
    return {"status": "healthy", "version": "2.0.0"}
