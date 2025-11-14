"""
Schemas Pydantic para lecciones y exámenes
"""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class LeccionDetalle(BaseModel):
    id: int
    titulo: str
    contenido_markdown: str
    ejemplos_codigo: Optional[str]
    puntos_clave: str
    duracion_estimada: int
    
    class Config:
        from_attributes = True

class MarcarLeccionCompletada(BaseModel):
    usuario_id: int
    leccion_id: int

class ProgresoResponse(BaseModel):
    lecciones_completadas: int
    total_lecciones: int
    porcentaje: float
    examenes_realizados: int
    promedio_nota: float

class PreguntaQuiz(BaseModel):
    id: int
    texto_pregunta: str
    tipo: str
    opciones: List[str]
    
class QuizResponse(BaseModel):
    leccion_id: int
    titulo_leccion: str
    preguntas: List[PreguntaQuiz]

class IntentoExamen(BaseModel):
    usuario_id: int
    respuestas: Dict[int, str]  # {pregunta_id: respuesta_elegida}

class ResultadoExamen(BaseModel):
    nota: float
    correctas: int
    incorrectas: int
    feedback: str
    detalles: List[Dict[str, Any]]
