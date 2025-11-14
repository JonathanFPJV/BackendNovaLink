"""
Endpoints de gestión de cursos
"""
import os
import shutil
import json
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import Curso, Leccion, Pregunta
from app.schemas.curso import CursoResponse, CursoDetalle, LeccionSimple
from app.services.pdf_service import extraer_texto_pdf
from app.services.ai_service import generar_lecciones_interactivas, generar_examen_dinamico
from app.utils.database import get_db

router = APIRouter(prefix="/cursos", tags=["Cursos"])

@router.post("/", response_model=dict)
async def crear_curso(
    nombre: str = Form(...), 
    proveedor: str = Form(...), 
    archivo: UploadFile = File(...),
    num_lecciones: int = Form(5),
    num_preguntas: int = Form(10),
    db: Session = Depends(get_db)
):
    """
    🎯 Crea un curso completo a partir de un PDF.
    ✅ Extrae texto del PDF
    ✅ Genera lecciones interactivas con IA
    ✅ Crea preguntas de evaluación automáticas
    """
    
    try:
        # 1. Validar archivo PDF
        if not archivo.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")
        
        # 2. Guardar PDF
        upload_dir = os.getenv("UPLOAD_DIR", "files")
        os.makedirs(upload_dir, exist_ok=True)
        ruta_pdf = f"{upload_dir}/{archivo.filename}"
        
        with open(ruta_pdf, "wb") as buffer:
            shutil.copyfileobj(archivo.file, buffer)
        
        print(f"✅ PDF guardado en: {ruta_pdf}")
        
        # 3. Extraer texto del PDF
        try:
            texto = extraer_texto_pdf(ruta_pdf)
            if not texto or len(texto) < 100:
                raise HTTPException(
                    status_code=400, 
                    detail="El PDF no contiene texto suficiente o no se pudo extraer"
                )
            print(f"✅ Texto extraído: {len(texto)} caracteres")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error extrayendo texto del PDF: {str(e)}")
        
        # 4. Crear curso en BD
        nuevo_curso = Curso(
            nombre=nombre, 
            proveedor=proveedor, 
            contenido_texto=texto[:5000]  # Limitar tamaño en BD
        )
        db.add(nuevo_curso)
        db.commit()
        db.refresh(nuevo_curso)
        print(f"✅ Curso creado con ID: {nuevo_curso.id}")
        
        lecciones_creadas = []
        preguntas_creadas = []
        
        # 5. Generar lecciones interactivas con IA
        try:
            print(f"🤖 Generando {num_lecciones} lecciones con IA...")
            lecciones_generadas = generar_lecciones_interactivas(texto, num_lecciones=num_lecciones)
            
            if not lecciones_generadas or len(lecciones_generadas) == 0:
                print("⚠️ No se generaron lecciones")
            else:
                for lec in lecciones_generadas:
                    nueva_leccion = Leccion(
                        curso_id=nuevo_curso.id,
                        titulo=lec.get("titulo", "Sin título"),
                        orden=lec.get("orden", 1),
                        contenido_markdown=lec.get("contenido_markdown", ""),
                        ejemplos_codigo=json.dumps(lec.get("ejemplos_codigo", [])),
                        puntos_clave=json.dumps(lec.get("puntos_clave", [])),
                        duracion_estimada=lec.get("duracion_estimada", 5)
                    )
                    db.add(nueva_leccion)
                    lecciones_creadas.append(nueva_leccion)
                
                db.commit()
                print(f"✅ {len(lecciones_creadas)} lecciones guardadas")
        
        except Exception as e:
            print(f"⚠️ Error generando lecciones: {str(e)}")
            # Continuar aunque falle la generación de lecciones
        
        # 6. Generar preguntas de evaluación con IA
        try:
            print(f"🤖 Generando {num_preguntas} preguntas con IA...")
            preguntas_generadas = generar_examen_dinamico(texto, cantidad=num_preguntas)
            
            if not preguntas_generadas or len(preguntas_generadas) == 0:
                print("⚠️ No se generaron preguntas")
            else:
                for p in preguntas_generadas:
                    nueva_pregunta = Pregunta(
                        curso_id=nuevo_curso.id,
                        tipo=p.get("tipo", "multiple"),
                        texto_pregunta=p.get("pregunta", ""),
                        opciones_json=json.dumps(p.get("opciones", [])),
                        respuesta_correcta=p.get("correcta", ""),
                        explicacion_feedback=p.get("explicacion", ""),
                        dificultad=p.get("dificultad", "media")
                    )
                    db.add(nueva_pregunta)
                    preguntas_creadas.append(nueva_pregunta)
                
                db.commit()
                print(f"✅ {len(preguntas_creadas)} preguntas guardadas")
        
        except Exception as e:
            print(f"⚠️ Error generando preguntas: {str(e)}")
            # Continuar aunque falle la generación de preguntas
        
        # 7. Respuesta final
        return {
            "mensaje": "✅ Curso creado exitosamente con IA",
            "curso": {
                "id": nuevo_curso.id,
                "nombre": nuevo_curso.nombre,
                "proveedor": nuevo_curso.proveedor
            },
            "estadisticas": {
                "lecciones_generadas": len(lecciones_creadas),
                "preguntas_generadas": len(preguntas_creadas),
                "caracteres_extraidos": len(texto)
            },
            "lecciones": [
                {
                    "id": l.id,
                    "titulo": l.titulo,
                    "orden": l.orden,
                    "duracion_estimada": l.duracion_estimada
                } for l in lecciones_creadas
            ],
            "archivo_pdf": ruta_pdf
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Error creando curso: {str(e)}"
        )

@router.get("/", response_model=list)
def listar_cursos(db: Session = Depends(get_db)):
    """Lista todos los cursos disponibles"""
    cursos = db.query(Curso).all()
    
    resultado = []
    for curso in cursos:
        num_lecciones = db.query(Leccion).filter(Leccion.curso_id == curso.id).count()
        num_preguntas = db.query(Pregunta).filter(Pregunta.curso_id == curso.id).count()
        
        resultado.append({
            "id": curso.id,
            "nombre": curso.nombre,
            "proveedor": curso.proveedor,
            "num_lecciones": num_lecciones,
            "num_preguntas": num_preguntas
        })
    
    return resultado

@router.get("/{curso_id}", response_model=dict)
def obtener_curso(curso_id: int, db: Session = Depends(get_db)):
    """Obtiene información detallada de un curso"""
    curso = db.query(Curso).filter(Curso.id == curso_id).first()
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    
    lecciones = db.query(Leccion).filter(Leccion.curso_id == curso.id).order_by(Leccion.orden).all()
    num_preguntas = db.query(Pregunta).filter(Pregunta.curso_id == curso.id).count()
    
    lecciones_data = [
        {
            "id": lec.id,
            "titulo": lec.titulo,
            "orden": lec.orden,
            "duracion_estimada": lec.duracion_estimada
        }
        for lec in lecciones
    ]
    
    return {
        "id": curso.id,
        "nombre": curso.nombre,
        "proveedor": curso.proveedor,
        "lecciones": lecciones_data,
        "estadisticas": {
            "total_lecciones": len(lecciones),
            "total_preguntas": num_preguntas
        }
    }

@router.delete("/{curso_id}", response_model=dict)
def eliminar_curso(curso_id: int, db: Session = Depends(get_db)):
    """
    🗑️ Elimina un curso y TODOS sus datos relacionados en cascada:
    - Lecciones del curso
    - Preguntas del examen
    - Progreso de lecciones de estudiantes
    - Progreso de exámenes de estudiantes
    """
    from app.models.database import ProgresoLeccion, Progreso
    
    # Verificar que el curso existe
    curso = db.query(Curso).filter(Curso.id == curso_id).first()
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    
    try:
        # Contar elementos antes de eliminar
        num_lecciones = db.query(Leccion).filter(Leccion.curso_id == curso_id).count()
        num_preguntas = db.query(Pregunta).filter(Pregunta.curso_id == curso_id).count()
        num_progreso_lecciones = db.query(ProgresoLeccion).filter(ProgresoLeccion.curso_id == curso_id).count()
        num_progreso_examenes = db.query(Progreso).filter(Progreso.curso_id == curso_id).count()
        
        # 1. Eliminar progreso de lecciones
        db.query(ProgresoLeccion).filter(ProgresoLeccion.curso_id == curso_id).delete()
        print(f"🗑️ Eliminados {num_progreso_lecciones} registros de progreso de lecciones")
        
        # 2. Eliminar progreso de exámenes
        db.query(Progreso).filter(Progreso.curso_id == curso_id).delete()
        print(f"🗑️ Eliminados {num_progreso_examenes} registros de progreso de exámenes")
        
        # 3. Eliminar lecciones
        db.query(Leccion).filter(Leccion.curso_id == curso_id).delete()
        print(f"🗑️ Eliminadas {num_lecciones} lecciones")
        
        # 4. Eliminar preguntas
        db.query(Pregunta).filter(Pregunta.curso_id == curso_id).delete()
        print(f"🗑️ Eliminadas {num_preguntas} preguntas")
        
        # 5. Eliminar el curso
        db.delete(curso)
        db.commit()
        print(f"✅ Curso '{curso.nombre}' eliminado completamente")
        
        return {
            "mensaje": f"✅ Curso '{curso.nombre}' eliminado exitosamente",
            "curso_id": curso_id,
            "elementos_eliminados": {
                "lecciones": num_lecciones,
                "preguntas": num_preguntas,
                "progreso_lecciones": num_progreso_lecciones,
                "progreso_examenes": num_progreso_examenes
            }
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando curso: {str(e)}"
        )
