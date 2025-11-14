"""
Servicio de integración con IA (Google Gemini)
"""
import os
import google.generativeai as genai
import json

# Configurar API de Google
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def generar_lecciones_interactivas(texto_curso: str, num_lecciones: int = 5):
    """
    Genera lecciones interactivas y fáciles de aprender basadas en el contenido del curso.
    Cada lección incluye: título, contenido explicativo, ejemplos prácticos y puntos clave.
    """
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Genera {num_lecciones} lecciones educativas en formato JSON.
    
    REGLAS ESTRICTAS:
    1. Responde SOLO con JSON válido (sin markdown, sin texto extra)
    2. Usa \\n para saltos de línea en strings
    3. Escapa comillas dobles con \\"
    4. No uses caracteres de control especiales
    5. Mantén contenido_markdown simple (máximo 500 caracteres)
    
    FORMATO:
    [
      {{
        "titulo": "Titulo de leccion",
        "orden": 1,
        "contenido_markdown": "Texto explicativo breve",
        "puntos_clave": ["Punto 1", "Punto 2", "Punto 3"],
        "duracion_estimada": 7
      }}
    ]
    
    CONTENIDO:
    {texto_curso[:8000]}
    """
    
    try:
        print(f"🤖 Llamando a Gemini para generar {num_lecciones} lecciones...")
        response = model.generate_content(prompt)
        
        if not response or not response.text:
            print("❌ Gemini no devolvió respuesta")
            return []
        
        print(f"✅ Respuesta recibida de Gemini ({len(response.text)} caracteres)")
        
        # Limpieza agresiva del JSON
        texto = response.text
        texto = texto.replace("```json", "").replace("```", "")
        texto = texto.strip()
        
        # Remover caracteres de control problemáticos
        import re
        texto = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', texto)  # Quitar control chars
        texto = texto.replace('\\n', ' ')  # Convertir \n a espacios
        texto = texto.replace('\n', ' ')   # Convertir saltos reales a espacios
        texto = re.sub(r'\s+', ' ', texto)  # Normalizar espacios
        
        print(f"🧹 JSON limpiado: {len(texto)} caracteres")
        
        lecciones = json.loads(texto)
        print(f"✅ {len(lecciones)} lecciones parseadas correctamente")
        return lecciones
        
    except json.JSONDecodeError as e:
        print(f"❌ Error parseando JSON de lecciones: {e}")
        print(f"Texto limpio (primeros 500): {texto[:500]}...")
        # Intentar parsear manualmente o retornar vacío
        return []
    except Exception as e:
        print(f"❌ Error generando lecciones: {e}")
        return []

def generar_examen_dinamico(texto_curso: str, cantidad: int = 10, enfoque: str = "general"):
    """
    Genera preguntas variadas para evaluar el aprendizaje.
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
        print(f"🤖 Llamando a Gemini para generar {cantidad} preguntas...")
        response = model.generate_content(prompt)
        
        if not response or not response.text:
            print("❌ Gemini no devolvió respuesta")
            return []
        
        print(f"✅ Respuesta recibida de Gemini ({len(response.text)} caracteres)")
        texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
        
        preguntas = json.loads(texto_limpio)
        print(f"✅ {len(preguntas)} preguntas parseadas correctamente")
        return preguntas
        
    except json.JSONDecodeError as e:
        print(f"❌ Error parseando JSON de preguntas: {e}")
        print(f"Respuesta de IA: {response.text[:500]}...")
        return []
    except Exception as e:
        print(f"❌ Error generando preguntas: {e}")
        return []

def generar_feedback_final(puntaje: int, temas_fallados: list):
    """Genera un consejo motivacional basado en la nota"""
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    Un estudiante obtuvo {puntaje}/100 en su examen. Falló en preguntas sobre: {temas_fallados}.
    Dame un feedback corto (max 2 lineas), constructivo y motivador. Dile qué debe repasar.
    """
    response = model.generate_content(prompt)
    return response.text
