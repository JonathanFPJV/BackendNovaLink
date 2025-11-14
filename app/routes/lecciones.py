"""
Endpoints de lecciones y progreso
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.database import Leccion, ProgresoLeccion, Curso
from app.schemas.leccion import LeccionDetalle, MarcarLeccionCompletada, ProgresoResponse
from app.utils.database import get_db

router = APIRouter(prefix="/lecciones", tags=["Lecciones"])

@router.get("/{leccion_id}", response_model=dict)
def obtener_leccion(leccion_id: int, db: Session = Depends(get_db)):
    """
    Devuelve el contenido detallado de una lección.
    Incluye contenido markdown, ejemplos de código y puntos clave.
    """
    leccion = db.query(Leccion).filter(Leccion.id == leccion_id).first()
    
    if not leccion:
        raise HTTPException(status_code=404, detail="Lección no encontrada")
    
    return {
        "id": leccion.id,
        "titulo": leccion.titulo,
        "contenido": leccion.contenido_markdown,
        "ejemplos": json.loads(leccion.ejemplos_codigo) if leccion.ejemplos_codigo else [],
        "puntos_clave": json.loads(leccion.puntos_clave) if leccion.puntos_clave else [],
        "duracion_minutos": leccion.duracion_estimada,
        "orden": leccion.orden
    }

@router.post("/completar", response_model=dict)
def marcar_leccion_completada(datos: MarcarLeccionCompletada, db: Session = Depends(get_db)):
    """
    Registra que un usuario completó una lección.
    Útil para hacer seguimiento del progreso de aprendizaje.
    """
    # Verificar si ya existe un registro
    progreso_existente = db.query(ProgresoLeccion).filter(
        ProgresoLeccion.usuario_id == datos.usuario_id,
        ProgresoLeccion.leccion_id == datos.leccion_id
    ).first()
    
    if progreso_existente:
        if not progreso_existente.completada:
            progreso_existente.completada = True
            progreso_existente.fecha_completada = datetime.now()
            db.commit()
    else:
        nuevo_progreso = ProgresoLeccion(
            usuario_id=datos.usuario_id,
            leccion_id=datos.leccion_id,
            completada=True,
            fecha_completada=datetime.now()
        )
        db.add(nuevo_progreso)
        db.commit()
    
    return {"mensaje": "Lección completada", "progreso_registrado": True}

@router.get("/curso/{curso_id}/lecciones", response_model=list)
def obtener_lecciones_curso(curso_id: int, db: Session = Depends(get_db)):
    """
    Devuelve todas las lecciones de un curso, ordenadas secuencialmente.
    """
    lecciones = db.query(Leccion).filter(Leccion.curso_id == curso_id).order_by(Leccion.orden).all()
    
    resultado = []
    for lec in lecciones:
        resultado.append({
            "id": lec.id,
            "titulo": lec.titulo,
            "orden": lec.orden,
            "contenido": lec.contenido_markdown,
            "ejemplos": json.loads(lec.ejemplos_codigo) if lec.ejemplos_codigo else [],
            "puntos_clave": json.loads(lec.puntos_clave) if lec.puntos_clave else [],
            "duracion_minutos": lec.duracion_estimada
        })
    
    return resultado

@router.get("/curso/{curso_id}/progreso/{usuario_id}", response_model=dict)
def obtener_progreso_curso(curso_id: int, usuario_id: int, db: Session = Depends(get_db)):
    """
    Devuelve el progreso del usuario en un curso específico.
    Muestra qué lecciones ha completado.
    """
    lecciones = db.query(Leccion).filter(Leccion.curso_id == curso_id).all()
    
    progreso_info = []
    for leccion in lecciones:
        progreso = db.query(ProgresoLeccion).filter(
            ProgresoLeccion.leccion_id == leccion.id,
            ProgresoLeccion.usuario_id == usuario_id
        ).first()
        
        progreso_info.append({
            "leccion_id": leccion.id,
            "titulo": leccion.titulo,
            "orden": leccion.orden,
            "completada": progreso.completada if progreso else False,
            "tiempo_dedicado": progreso.tiempo_dedicado if progreso else 0
        })
    
    total_lecciones = len(lecciones)
    completadas = sum(1 for p in progreso_info if p["completada"])
    porcentaje = int((completadas / total_lecciones) * 100) if total_lecciones > 0 else 0
    
    return {
        "progreso_lecciones": progreso_info,
        "estadisticas": {
            "total_lecciones": total_lecciones,
            "completadas": completadas,
            "porcentaje_completado": porcentaje
        }
    }
