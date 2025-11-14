"""
Endpoints de autenticación
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.auth import (
    RegistroUsuario, 
    LoginUsuario, 
    TokenGoogle, 
    UsuarioSimple,
    RespuestaUsuario
)
from app.services import auth_service
from app.utils.database import get_db

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/registro", response_model=dict)
def registro_usuario(datos: RegistroUsuario, db: Session = Depends(get_db)):
    """
    Registra un nuevo usuario con email y contraseña.
    La contraseña se almacena hasheada (bcrypt) de forma segura.
    """
    usuario = auth_service.registrar_usuario(db, datos)
    
    return {
        "mensaje": "Usuario registrado exitosamente",
        "user_id": usuario.id,
        "nombre": usuario.nombre,
        "email": usuario.email
    }

@router.post("/login", response_model=dict)
def login_usuario(datos: LoginUsuario, db: Session = Depends(get_db)):
    """
    Login tradicional con email y contraseña.
    Verifica las credenciales y devuelve la información del usuario.
    """
    usuario = auth_service.login_con_password(db, datos)
    
    return {
        "mensaje": "Login exitoso",
        "user_id": usuario.id,
        "nombre": usuario.nombre,
        "email": usuario.email,
        "foto": usuario.foto_url
    }

@router.post("/google-login", response_model=dict)
def login_google(datos: TokenGoogle, db: Session = Depends(get_db)):
    """
    Login con Google OAuth.
    Valida el token de Google y crea/actualiza el usuario.
    """
    usuario = auth_service.login_con_google(db, datos.token)
    
    return {
        "mensaje": "Login exitoso",
        "user_id": usuario.id,
        "nombre": usuario.nombre,
        "email": usuario.email,
        "foto": usuario.foto_url
    }

@router.post("/login-simple", response_model=dict)
def login_simple(datos: UsuarioSimple, db: Session = Depends(get_db)):
    """
    Login simple para prototipos.
    No requiere validación de contraseña.
    """
    usuario = auth_service.login_simple(
        db, 
        datos.identificador, 
        datos.nombre, 
        datos.foto_url
    )
    
    return {
        "mensaje": "Login exitoso",
        "user_id": usuario.id,
        "nombre": usuario.nombre
    }
