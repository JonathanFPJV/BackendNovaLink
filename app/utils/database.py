"""
Configuración de base de datos SQLAlchemy
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Crear el motor de conexión
engine = create_engine(
    settings.DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Solo para SQLite
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
