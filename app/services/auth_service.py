"""
Servicio de autenticación y gestión de usuarios
"""
import os
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.database import Usuario
from app.schemas.auth import RegistroUsuario, LoginUsuario
from app.utils.security import hash_password, verify_password
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

def validar_token_google(token: str):
    """Valida un token de Google y devuelve la información del usuario"""
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not google_client_id:
        return None
    try:
        info = id_token.verify_oauth2_token(
            token, 
            google_requests.Request(), 
            google_client_id
        )
        return info
    except Exception as e:
        print(f"Error validando token Google: {e}")
        return None

def registrar_usuario(db: Session, datos: RegistroUsuario):
    """Registra un nuevo usuario con email y contraseña"""
    # Verificar si el email ya existe
    usuario_existente = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # Hashear la contraseña
    password_hasheada = hash_password(datos.password)
    
    # Crear nuevo usuario
    nuevo_usuario = Usuario(
        nombre=datos.nombre,
        email=datos.email,
        password_hash=password_hasheada,
        tipo_auth="password"
    )
    
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    
    return nuevo_usuario

def login_con_password(db: Session, datos: LoginUsuario):
    """Login tradicional con email y contraseña"""
    # Buscar usuario por email
    usuario = db.query(Usuario).filter(Usuario.email == datos.email).first()
    
    if not usuario:
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
    
    # Verificar que el usuario tenga contraseña configurada
    if not usuario.password_hash:
        raise HTTPException(status_code=401, detail="Este usuario usa otro método de autenticación")
    
    # Verificar la contraseña
    if not verify_password(datos.password, usuario.password_hash):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
    
    # Verificar que el usuario esté activo
    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Usuario desactivado")
    
    return usuario

def login_con_google(db: Session, token: str):
    """Login con Google OAuth"""
    info_usuario = validar_token_google(token)
    
    if not info_usuario:
        raise HTTPException(status_code=401, detail="Token de Google inválido")
    
    email = info_usuario.get("email")
    nombre = info_usuario.get("name")
    foto = info_usuario.get("picture")
    google_id = info_usuario.get("sub")
    
    # Buscar por identificador externo (Google ID)
    usuario = db.query(Usuario).filter(Usuario.identificador_externo == google_id).first()
    
    if not usuario:
        usuario = Usuario(
            email=email, 
            nombre=nombre, 
            foto_url=foto,
            identificador_externo=google_id,
            tipo_auth="google"
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
    
    return usuario

def login_simple(db: Session, identificador: str, nombre: str, foto_url: str = None):
    """Login simple para prototipos sin validación estricta"""
    usuario = db.query(Usuario).filter(
        Usuario.identificador_externo == identificador
    ).first()
    
    if not usuario:
        usuario = Usuario(
            nombre=nombre,
            identificador_externo=identificador,
            foto_url=foto_url,
            tipo_auth="test"
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
    
    return usuario
