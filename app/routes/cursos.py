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
    generar_lecciones: bool = Form(True),
    db: Session = Depends(get_db)
):
    """
    Crea un curso a partir de un PDF.
    Genera lecciones interactivas para aprender y preguntas para evaluar.
    """
    # 1. Guardar PDF
    upload_dir = os.getenv("UPLOAD_DIR", "files")
    os.makedirs(upload_dir, exist_ok=True)
    ruta_pdf = f"{upload_dir}/{archivo.filename}"
    with open(ruta_pdf, "wb") as buffer:
        shutil.copyfileobj(archivo.file, buffer)
    
    # 2. Extraer texto
    texto = extraer_texto_pdf(ruta_pdf)
    
    # 3. Crear curso
    nuevo_curso = Curso(nombre=nombre, proveedor=proveedor, contenido_texto=texto)
    db.add(nuevo_curso)
    db.commit()
    db.refresh(nuevo_curso)
    
    lecciones_creadas = 0
    preguntas_creadas = 0
    
    # 4. Generar lecciones interactivas
    if generar_lecciones:
        lecciones_generadas = generar_lecciones_interactivas(texto, num_lecciones=5)
        
        for lec in lecciones_generadas:
            nueva_leccion = Leccion(
                curso_id=nuevo_curso.id,
                titulo=lec["titulo"],
                orden=lec["orden"],
                contenido_markdown=lec["contenido_markdown"],
                ejemplos_codigo=json.dumps(lec.get("ejemplos_codigo", [])),
                puntos_clave=json.dumps(lec.get("puntos_clave", [])),
                duracion_estimada=lec.get("duracion_estimada", 5)
            )
            db.add(nueva_leccion)
            lecciones_creadas += 1
        
        db.commit()
    
    # 5. Generar preguntas
    preguntas_generadas = generar_examen_dinamico(texto, cantidad=10)
    
    for p in preguntas_generadas:
        nueva_pregunta = Pregunta(
            curso_id=nuevo_curso.id,
            tipo=p.get("tipo", "multiple"),
            texto_pregunta=p["pregunta"],
            opciones_json=json.dumps(p.get("opciones", [])),
            respuesta_correcta=p["correcta"],
            explicacion_feedback=p["explicacion"],
            dificultad=p.get("dificultad", "media")
        )
        db.add(nueva_pregunta)
        preguntas_creadas += 1
    
    db.commit()
    
    return {
        "mensaje": "Curso creado exitosamente",
        "curso_id": nuevo_curso.id,
        "lecciones_generadas": lecciones_creadas,
        "preguntas_generadas": preguntas_creadas
    }

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
