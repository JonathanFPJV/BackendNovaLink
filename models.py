from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# 1. Tabla CURSOS
class Curso(Base):
    __tablename__ = "cursos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    proveedor = Column(String)
    # NUEVO: Guardamos el texto extraído para reutilizarlo en reintentos
    contenido_texto = Column(Text) 
    
    preguntas = relationship("Pregunta", back_populates="curso")

class Pregunta(Base):
    __tablename__ = "preguntas"
    id = Column(Integer, primary_key=True, index=True)
    curso_id = Column(Integer, ForeignKey("cursos.id"))
    
    # NUEVO: Tipo de pregunta ('multiple', 'completar', 'verdadero_falso')
    tipo = Column(String, default="multiple") 
    
    texto_pregunta = Column(Text)
    # Para 'completar', aquí guardamos las palabras distractoras también
    opciones_json = Column(Text) 
    respuesta_correcta = Column(String)
    explicacion_feedback = Column(Text)
    
    curso = relationship("Curso", back_populates="preguntas")
    # Relación con los intentos/progreso de los estudiantes
    intentos = relationship("Progreso", back_populates="pregunta")

# 3. Tabla PROGRESO (Intentos del estudiante)
class Progreso(Base):
    __tablename__ = "progreso"
    id = Column(Integer, primary_key=True, index=True)
    # Nota: Para el MVP simplificado, usaremos un user_id genérico (ej: 1)
    usuario_id = Column(Integer, default=1) 
    pregunta_id = Column(Integer, ForeignKey("preguntas.id"))
    
    respuesta_elegida = Column(String)
    es_correcto = Column(Boolean)
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    
    pregunta = relationship("Pregunta", back_populates="intentos")