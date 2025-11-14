"""
Configuración de base de datos SQLAlchemy
Detecta automáticamente si usar SQLite (local) o PostgreSQL (Render)
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 🔧 Detectar entorno: Local (SQLite) o Render (PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    # 🚨 FIX para Render: Cambiar postgres:// a postgresql://
    # Render/Heroku usan postgres:// pero SQLAlchemy requiere postgresql://
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    print("🐘 Usando PostgreSQL (Render)")
elif DATABASE_URL:
    print(f"💾 Usando: {DATABASE_URL}")
else:
    # Desarrollo local: SQLite
    DATABASE_URL = "sqlite:///./techbridge.db"
    print("💻 Usando SQLite (Local)")

# Configurar argumentos según el tipo de base de datos
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Crear el motor de conexión
engine = create_engine(
    DATABASE_URL, 
    connect_args=connect_args,
    pool_pre_ping=True,  # Verificar conexiones antes de usar
    echo=False  # Cambiar a True para debug SQL
)

print(f"✅ Motor de BD configurado: {engine.url.drivername}")

# Crear la sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para crear los modelos
Base = declarative_base()

# Dependencia para obtener la base de datos en cada request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
