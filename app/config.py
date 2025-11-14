"""
Configuración centralizada de la aplicación
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Base de datos
    DATABASE_URL = "sqlite:///./techbridge.db"
    
    # APIs externas
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_CLIENT_ID = os.getenv("CLIENT_ID", "")
    
    # CORS
    ALLOWED_ORIGINS = ["*"]  # En producción especificar dominios exactos
    
    # Directorios
    UPLOAD_DIR = "files"
    
    # Seguridad
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

settings = Settings()
