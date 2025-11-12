import shutil
import os
import json
from typing import Dict
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

# --- IMPORTANTE: Asegúrate de que tus imports coincidan con tus archivos actualizados ---
from database import engine, get_db, Base
from models import Curso, Pregunta, Progreso
# Nota: Aquí importamos las nuevas funciones que creamos en el paso anterior
from ai_service import extraer_texto_pdf, generar_examen_dinamico, generar_feedback_final

# Crear las tablas en la BD al iniciar
Base.metadata.create_all(bind=engine)

app = FastAPI(title="API TechBridge MVP - Final")

# --- ESQUEMAS DE DATOS (Pydantic) ---

class RespuestaUsuario(BaseModel):
    pregunta_id: int
    respuesta: str

# Esquema para recibir el examen completo
class IntentoExamen(BaseModel):
    usuario_id: int
    # Diccionario: { "ID_Pregunta": "Respuesta_Usuario" }
    respuestas: Dict[int, str] 

# --- ENDPOINT 1: SUBIR CURSO Y GENERAR EXAMEN DINÁMICO ---
@app.post("/crear-curso/")
async def crear_curso(
    nombre: str = Form(...), 
    proveedor: str = Form(...), 
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. Guardar PDF localmente
    os.makedirs("files", exist_ok=True)
    ruta_pdf = f"files/{archivo.filename}"
    with open(ruta_pdf, "wb") as buffer:
        shutil.copyfileobj(archivo.file, buffer)
    
    # 2. Procesar texto del PDF
    texto = extraer_texto_pdf(ruta_pdf)
    
    # 3. Guardar Curso en BD (Incluyendo el texto extraído para futuros reintentos)
    nuevo_curso = Curso(nombre=nombre, proveedor=proveedor, contenido_texto=texto)
    db.add(nuevo_curso)
    db.commit()
    db.refresh(nuevo_curso)
    
    # 4. Generar el primer examen (10 preguntas variadas con IA)
    # Usamos la función nueva 'generar_examen_dinamico'
    preguntas_generadas = generar_examen_dinamico(texto, cantidad=10)
    
    # 5. Guardar Preguntas en BD
    for p in preguntas_generadas:
        # Obtener opciones, con un valor por defecto para V/F si no existen
        opciones = p.get("opciones", ["Verdadero", "Falso"])
        
        nueva_pregunta = Pregunta(
            curso_id=nuevo_curso.id,
            tipo=p.get("tipo", "multiple"), # Si no viene el tipo, asumimos multiple
            texto_pregunta=p["pregunta"],
            opciones_json=json.dumps(opciones), # Convertir lista a texto JSON
            respuesta_correcta=p["correcta"],
            explicacion_feedback=p["explicacion"]
        )
        db.add(nueva_pregunta)
    db.commit()
    
    return {
        "mensaje": "Curso creado. Examen dinámico generado con éxito.", 
        "curso_id": nuevo_curso.id,
        "preguntas_generadas": len(preguntas_generadas)
    }

# --- ENDPOINT 2: OBTENER PREGUNTAS DE UN CURSO ---
@app.get("/curso/{curso_id}/quiz")
def obtener_quiz(curso_id: int, db: Session = Depends(get_db)):
    preguntas = db.query(Pregunta).filter(Pregunta.curso_id == curso_id).all()
    
    resultado = []
    for p in preguntas:
        resultado.append({
            "id": p.id,
            "tipo": p.tipo, # ¡Importante para que el Frontend sepa cómo dibujar la pregunta!
            "pregunta": p.texto_pregunta,
            "opciones": json.loads(p.opciones_json) # Convertir texto JSON a lista Python
        })
    return resultado

# --- ENDPOINT 3: CALIFICAR EXAMEN COMPLETO (NUEVO) ---
@app.post("/calificar-examen/")
def calificar_examen(intento: IntentoExamen, db: Session = Depends(get_db)):
    puntaje = 0
    total = 0
    temas_fallados = []
    
    # Iteramos sobre las respuestas enviadas por el usuario
    for preg_id, resp_usuario in intento.respuestas.items():
        pregunta = db.query(Pregunta).filter(Pregunta.id == preg_id).first()
        
        if pregunta:
            total += 1
            # Normalizamos respuestas (minúsculas y sin espacios extra) para comparar
            correcta = pregunta.respuesta_correcta.lower().strip()
            usuario = resp_usuario.lower().strip()
            
            if correcta == usuario:
                puntaje += 1
            else:
                # Si falló, guardamos la pregunta para que la IA sepa qué recomendar
                temas_fallados.append(pregunta.texto_pregunta)
    
    # Calcular nota final (0 a 100)
    nota_final = int((puntaje / total) * 100) if total > 0 else 0
    
    # Pedirle a la IA feedback global usando los temas fallados
    feedback_ia = generar_feedback_final(nota_final, temas_fallados)
    
    return {
        "nota": nota_final,
        "aciertos": puntaje,
        "total": total,
        "mensaje_ia": feedback_ia,
        "aprobado": nota_final >= 70
    }

# --- ENDPOINT 4: GENERAR REINTENTO (NUEVO) ---
@app.post("/generar-reintento/{curso_id}")
def generar_reintento(curso_id: int, db: Session = Depends(get_db)):
    curso = db.query(Curso).filter(Curso.id == curso_id).first()
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    
    if not curso.contenido_texto:
        raise HTTPException(status_code=400, detail="Este curso no tiene texto guardado para regenerar.")

    # 1. Borramos las preguntas viejas de este curso
    db.query(Pregunta).filter(Pregunta.curso_id == curso_id).delete()
    
    # 2. Generamos NUEVAS preguntas usando el texto guardado
    # Al ser IA generativa, las preguntas serán diferentes a las anteriores
    nuevas_preguntas = generar_examen_dinamico(curso.contenido_texto, cantidad=10)
    
    # 3. Guardamos las nuevas preguntas
    for p in nuevas_preguntas:
        nueva = Pregunta(
            curso_id=curso.id,
            tipo=p.get("tipo", "multiple"),
            texto_pregunta=p["pregunta"],
            opciones_json=json.dumps(p["opciones"]),
            respuesta_correcta=p["correcta"],
            explicacion_feedback=p["explicacion"]
        )
        db.add(nueva)
    db.commit()
    
    return {"mensaje": "Examen regenerado exitosamente. ¡Nuevas preguntas listas!"}

# --- ENDPOINT 5: RESPUESTA INDIVIDUAL (OPCIONAL, MANTENIDO POR COMPATIBILIDAD) ---
@app.post("/responder-individual/")
def responder_pregunta(datos: RespuestaUsuario, db: Session = Depends(get_db)):
    pregunta = db.query(Pregunta).filter(Pregunta.id == datos.pregunta_id).first()
    
    if not pregunta:
        raise HTTPException(status_code=404, detail="Pregunta no existe")
        
    es_correcto = (datos.respuesta.lower().strip() == pregunta.respuesta_correcta.lower().strip())
    
    # Guardar progreso individual
    intento = Progreso(
        usuario_id=1, # Usuario Dummy para MVP
        pregunta_id=datos.pregunta_id,
        respuesta_elegida=datos.respuesta,
        es_correcto=es_correcto
    )
    db.add(intento)
    db.commit()
    
    return {
        "es_correcto": es_correcto,
        "feedback": pregunta.explicacion_feedback if not es_correcto else "¡Correcto!"
    }