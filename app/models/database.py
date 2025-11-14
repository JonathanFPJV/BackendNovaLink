"""
Modelos de base de datos con SQLAlchemy
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.utils.database import Base

# --- 1. TABLA USUARIOS (Compatible con múltiples clientes: móvil, web) ---
class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    nombre = Column(String)
    foto_url = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)  # Contraseña hasheada (bcrypt)
    identificador_externo = Column(String, unique=True, index=True, nullable=True)
    tipo_auth = Column(String, default="email")  # email, google, password, test
    activo = Column(Boolean, default=True)
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    progreso = relationship("Progreso", back_populates="estudiante")
    progreso_lecciones = relationship("ProgresoLeccion", back_populates="usuario")

# 2. TABLA CURSOS
class Curso(Base):
    __tablename__ = "cursos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    proveedor = Column(String)
    contenido_texto = Column(Text)
    
    # Relaciones
    lecciones = relationship("Leccion", back_populates="curso", cascade="all, delete-orphan")
    preguntas = relationship("Pregunta", back_populates="curso", cascade="all, delete-orphan")

# 3. TABLA LECCIONES (Contenido interactivo generado por IA)
class Leccion(Base):
    __tablename__ = "lecciones"
    id = Column(Integer, primary_key=True, index=True)
    curso_id = Column(Integer, ForeignKey("cursos.id"))
    titulo = Column(String, index=True)
    orden = Column(Integer)
    contenido_markdown = Column(Text)
    ejemplos_codigo = Column(Text, nullable=True)
    puntos_clave = Column(Text)
    duracion_estimada = Column(Integer, default=5)
    
    curso = relationship("Curso", back_populates="lecciones")
    progreso_lecciones = relationship("ProgresoLeccion", back_populates="leccion")

# 4. TABLA PREGUNTAS (Pruebas para comprobar lo aprendido)
class Pregunta(Base):
    __tablename__ = "preguntas"
    id = Column(Integer, primary_key=True, index=True)
    curso_id = Column(Integer, ForeignKey("cursos.id"))
    leccion_id = Column(Integer, ForeignKey("lecciones.id"), nullable=True)
    tipo = Column(String, default="multiple")
    texto_pregunta = Column(Text)
    opciones_json = Column(Text)
    respuesta_correcta = Column(String)
    explicacion_feedback = Column(Text)
    dificultad = Column(String, default="media")
    
    curso = relationship("Curso", back_populates="preguntas")
    intentos = relationship("Progreso", back_populates="pregunta")

# 5. TABLA PROGRESO DE LECCIONES
class ProgresoLeccion(Base):
    __tablename__ = "progreso_lecciones"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    leccion_id = Column(Integer, ForeignKey("lecciones.id"))
    completada = Column(Boolean, default=False)
    tiempo_dedicado = Column(Integer, default=0)
    fecha_inicio = Column(DateTime(timezone=True), server_default=func.now())
    fecha_completada = Column(DateTime(timezone=True), nullable=True)
    
    usuario = relationship("Usuario", back_populates="progreso_lecciones")
    leccion = relationship("Leccion", back_populates="progreso_lecciones")

# 6. TABLA PROGRESO DE PREGUNTAS (Resultados de pruebas)
class Progreso(Base):
    __tablename__ = "progreso"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id")) 
    pregunta_id = Column(Integer, ForeignKey("preguntas.id"))
    respuesta_elegida = Column(String)
    es_correcto = Column(Boolean)
    intentos = Column(Integer, default=1)
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    
    estudiante = relationship("Usuario", back_populates="progreso")
    pregunta = relationship("Pregunta", back_populates="intentos")
