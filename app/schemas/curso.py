"""
Schemas Pydantic para cursos
"""
from pydantic import BaseModel
from typing import List, Optional

class CursoBase(BaseModel):
    nombre: str
    proveedor: str

class CursoResponse(BaseModel):
    id: int
    nombre: str
    proveedor: str
    total_lecciones: int
    
    class Config:
        from_attributes = True

class LeccionSimple(BaseModel):
    id: int
    titulo: str
    orden: int
    duracion_estimada: int
    
    class Config:
        from_attributes = True

class CursoDetalle(BaseModel):
    id: int
    nombre: str
    proveedor: str
    lecciones: List[LeccionSimple]
    
    class Config:
        from_attributes = True
