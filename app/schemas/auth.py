"""
Schemas Pydantic para autenticación
"""
from pydantic import BaseModel
from typing import Optional

class TokenGoogle(BaseModel):
    token: str

class UsuarioSimple(BaseModel):
    identificador: str
    nombre: str
    foto_url: Optional[str] = None

class RegistroUsuario(BaseModel):
    email: str
    nombre: str
    password: str

class LoginUsuario(BaseModel):
    email: str
    password: str

class RespuestaUsuario(BaseModel):
    id: int
    nombre: str
    email: Optional[str]
    
    class Config:
        from_attributes = True
