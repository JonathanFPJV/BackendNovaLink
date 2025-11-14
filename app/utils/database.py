"""
Configuración de base de datos SQLAlchemy
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Obtener DATABASE_URL directamente de variable de entorno o usar SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./techbridge.db")

# Configurar argumentos según el tipo de base de datos
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Crear el motor de conexión
engine = create_engine(
    DATABASE_URL, 
    connect_args=connect_args,
    pool_pre_ping=True  # Verificar conexiones antes de usar
)

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
