import google.generativeai as genai
from PyPDF2 import PdfReader
import json

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# --- ¡PON TU API KEY AQUÍ! ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)


def extraer_texto_pdf(ruta_archivo):
    """Lee un PDF y devuelve todo el texto como un string."""
    reader = PdfReader(ruta_archivo)
    texto_completo = ""
    for page in reader.pages:
        texto_completo += page.extract_text()
    return texto_completo

def generar_examen_dinamico(texto_curso, cantidad=10, enfoque="general"):
    """
    Genera preguntas variadas.
    enfoque: 'general' (todo el texto) o un tema específico si falló antes.
    """
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Eres un experto pedagogo en tecnología. Genera un examen de {cantidad} preguntas basado en el texto proporcionado.
    
    REGLAS DE CREATIVIDAD:
    1. Mezcla tipos de preguntas: 
       - "multiple" (Opción Múltiple clásica)
       - "completar" (Frase con un espacio en blanco ____ )
       - "verdadero_falso" (Indicar si una afirmación es cierta)
    2. Si es "completar", en 'opciones' pon la respuesta correcta y 3 palabras falsas para que el usuario elija.
    3. La salida debe ser EXCLUSIVAMENTE un JSON Array válido.

    FORMATO JSON ESPERADO:
    [
        {{
            "tipo": "multiple",
            "pregunta": "¿Qué protocolo es ligero?",
            "opciones": ["HTTP", "MQTT", "FTP"],
            "correcta": "MQTT",
            "explicacion": "MQTT está diseñado para bajo ancho de banda."
        }},
        {{
            "tipo": "completar",
            "pregunta": "El ____ Computing procesa datos cerca de la fuente.",
            "opciones": ["Edge", "Cloud", "Fog", "Mist"], 
            "correcta": "Edge",
            "explicacion": "Edge Computing reduce la latencia."
        }}
    ]

    TEXTO DE ESTUDIO ({enfoque}):
    {texto_curso[:20000]}
    """
    
    try:
        response = model.generate_content(prompt)
        texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(texto_limpio)
    except Exception as e:
        print(f"Error IA: {e}")
        return []

def generar_feedback_final(puntaje, temas_fallados):
    """Genera un consejo motivacional basado en la nota."""
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    Un estudiante obtuvo {puntaje}/100 en su examen. Falló en preguntas sobre: {temas_fallados}.
    Dame un feedback corto (max 2 lineas), constructivo y motivador. Dile qué debe repasar.
    """
    response = model.generate_content(prompt)
    return response.text