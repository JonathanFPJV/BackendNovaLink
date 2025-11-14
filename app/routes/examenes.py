"""
Endpoints de exámenes y evaluaciones
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import Pregunta, Progreso, Usuario, Curso, Leccion
from app.schemas.leccion import QuizResponse, IntentoExamen, ResultadoExamen, PreguntaQuiz
from app.services.ai_service import generar_feedback_final, generar_examen_dinamico
from app.utils.database import get_db

router = APIRouter(prefix="/examenes", tags=["Exámenes"])

@router.get("/leccion/{leccion_id}/quiz", response_model=dict)
def obtener_quiz_leccion(leccion_id: int, db: Session = Depends(get_db)):
    """
    Devuelve las preguntas asociadas a una lección específica.
    """
    leccion = db.query(Leccion).filter(Leccion.id == leccion_id).first()
    if not leccion:
        raise HTTPException(status_code=404, detail="Lección no encontrada")
    
    preguntas = db.query(Pregunta).filter(Pregunta.leccion_id == leccion_id).all()
    
    # Si no hay preguntas asociadas a la lección, buscar del curso
    if not preguntas:
        preguntas = db.query(Pregunta).filter(Pregunta.curso_id == leccion.curso_id).all()
    
    resultado = []
    for p in preguntas:
        resultado.append({
            "id": p.id,
            "tipo": p.tipo,
            "pregunta": p.texto_pregunta,
            "opciones": json.loads(p.opciones_json),
            "dificultad": p.dificultad
        })
    
    return {
        "leccion_id": leccion_id,
        "titulo_leccion": leccion.titulo,
        "preguntas": resultado
    }

@router.get("/curso/{curso_id}/quiz", response_model=list)
def obtener_quiz_curso(curso_id: int, db: Session = Depends(get_db)):
    """
    Devuelve todas las preguntas del curso para realizar la prueba.
    """
    preguntas = db.query(Pregunta).filter(Pregunta.curso_id == curso_id).all()
    
    resultado = []
    for p in preguntas:
        resultado.append({
            "id": p.id,
            "tipo": p.tipo,
            "pregunta": p.texto_pregunta,
            "opciones": json.loads(p.opciones_json),
            "dificultad": p.dificultad
        })
    return resultado

@router.post("/calificar", response_model=dict)
def calificar_examen(intento: IntentoExamen, db: Session = Depends(get_db)):
    """
    Califica todas las respuestas del examen y da feedback con IA.
    Guarda el progreso del estudiante.
    """
    # Extraer usuario_id de las respuestas si está presente
    # El schema debe incluir usuario_id
    if not hasattr(intento, 'usuario_id'):
        raise HTTPException(status_code=400, detail="Falta usuario_id en el intento")
    
    usuario = db.query(Usuario).filter(Usuario.id == intento.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    puntaje = 0
    total = 0
    temas_fallados = []
    detalles = []
    
    for preg_id, resp_usuario in intento.respuestas.items():
        pregunta = db.query(Pregunta).filter(Pregunta.id == preg_id).first()
        
        if pregunta:
            total += 1
            correcta = pregunta.respuesta_correcta.lower().strip()
            respuesta_normalizada = resp_usuario.lower().strip()
            
            es_correcto = (correcta == respuesta_normalizada)
            
            if es_correcto:
                puntaje += 1
            else:
                temas_fallados.append(pregunta.texto_pregunta)
            
            detalles.append({
                "pregunta": pregunta.texto_pregunta,
                "respuesta_usuario": resp_usuario,
                "respuesta_correcta": pregunta.respuesta_correcta,
                "correcto": es_correcto,
                "explicacion": pregunta.explicacion_feedback
            })
            
            # Guardar progreso
            progreso_existente = db.query(Progreso).filter(
                Progreso.usuario_id == intento.usuario_id,
                Progreso.pregunta_id == preg_id
            ).first()
            
            if progreso_existente:
                progreso_existente.intentos += 1
                progreso_existente.respuesta_elegida = resp_usuario
                progreso_existente.es_correcto = es_correcto
            else:
                nuevo_progreso = Progreso(
                    usuario_id=intento.usuario_id,
                    pregunta_id=preg_id,
                    respuesta_elegida=resp_usuario,
                    es_correcto=es_correcto
                )
                db.add(nuevo_progreso)
    
    db.commit()
    
    nota_final = int((puntaje / total) * 100) if total > 0 else 0
    feedback_ia = generar_feedback_final(nota_final, temas_fallados)
    
    return {
        "nota": nota_final,
        "correctas": puntaje,
        "incorrectas": total - puntaje,
        "feedback": feedback_ia,
        "detalles": detalles
    }

@router.post("/curso/{curso_id}/regenerar", response_model=dict)
def generar_reintento(curso_id: int, cantidad: int = 10, db: Session = Depends(get_db)):
    """
    🔄 Regenera nuevas preguntas para el curso.
    Útil cuando el estudiante quiere volver a practicar con preguntas diferentes.
    """
    # Verificar que el curso existe
    curso = db.query(Curso).filter(Curso.id == curso_id).first()
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    
    # Verificar que hay contenido
    if not curso.contenido_texto:
        raise HTTPException(
            status_code=400, 
            detail="El curso no tiene contenido. Sube un PDF primero."
        )
    
    try:
        # Eliminar preguntas antiguas
        preguntas_viejas = db.query(Pregunta).filter(Pregunta.curso_id == curso_id).all()
        num_eliminadas = len(preguntas_viejas)
        
        for p in preguntas_viejas:
            db.delete(p)
        
        print(f"🗑️ Eliminadas {num_eliminadas} preguntas antiguas")
        
        # Generar nuevas preguntas con IA
        print(f"🤖 Generando {cantidad} nuevas preguntas...")
        nuevas_preguntas = generar_examen_dinamico(curso.contenido_texto, cantidad=cantidad)
        
        if not nuevas_preguntas:
            raise HTTPException(
                status_code=500,
                detail="No se pudieron generar preguntas. Intenta nuevamente."
            )
        
        # Guardar nuevas preguntas
        preguntas_creadas = []
        for p in nuevas_preguntas:
            nueva = Pregunta(
                curso_id=curso_id,
                tipo=p.get("tipo", "multiple"),
                texto_pregunta=p.get("pregunta", ""),
                opciones_json=json.dumps(p.get("opciones", [])),
                respuesta_correcta=p.get("correcta", ""),
                explicacion_feedback=p.get("explicacion", ""),
                dificultad=p.get("dificultad", "media")
            )
            db.add(nueva)
            preguntas_creadas.append(nueva)
        
        db.commit()
        print(f"✅ {len(preguntas_creadas)} nuevas preguntas guardadas")
        
        # Refrescar para obtener IDs
        for p in preguntas_creadas:
            db.refresh(p)
        
        return {
            "mensaje": "✅ Examen regenerado exitosamente",
            "curso_id": curso_id,
            "curso_nombre": curso.nombre,
            "preguntas_eliminadas": num_eliminadas,
            "preguntas_generadas": len(preguntas_creadas),
            "preguntas": [
                {
                    "id": p.id,
                    "tipo": p.tipo,
                    "pregunta": p.texto_pregunta,
                    "opciones": json.loads(p.opciones_json),
                    "dificultad": p.dificultad
                }
                for p in preguntas_creadas
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Error regenerando examen: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error regenerando examen: {str(e)}"
        )
