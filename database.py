from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Nombre del archivo de base de datos local
SQLALCHEMY_DATABASE_URL = "sqlite:///./techbridge.db"

# Crear el motor de conexión (check_same_thread=False es necesario para SQLite)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Crear la sesión para hablar con la BD
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para crear los modelos
Base = declarative_base()

# Función utilitaria para obtener la base de datos en cada petición
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()