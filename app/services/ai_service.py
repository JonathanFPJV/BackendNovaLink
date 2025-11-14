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
    Eres un pedagogo experto en crear contenido educativo interactivo y fácil de entender.
    
    TAREA: Divide el siguiente contenido en {num_lecciones} lecciones progresivas y didácticas.
    
    REGLAS:
    1. Cada lección debe ser corta (5-10 minutos de lectura)
    2. Usa lenguaje simple y ejemplos prácticos del mundo real
    3. Incluye analogías y comparaciones para conceptos complejos
    4. Estructura cada lección con: introducción, desarrollo, ejemplos y resumen
    5. Los ejemplos de código deben ser simples y bien comentados
    
    FORMATO JSON ESPERADO:
    [
        {{
            "titulo": "Introducción a IoT y sus Aplicaciones",
            "orden": 1,
            "contenido_markdown": "# Introducción\\n\\n¿Qué es IoT?...\\n\\n## Conceptos Básicos\\n...",
            "ejemplos_codigo": [
                {{
                    "lenguaje": "python",
                    "descripcion": "Sensor de temperatura básico",
                    "codigo": "import sensor\\ntemp = sensor.read_temperature()\\nprint(temp)"
                }}
            ],
            "puntos_clave": [
                "IoT conecta dispositivos a internet",
                "Los sensores recopilan datos del entorno",
                "MQTT es un protocolo común en IoT"
            ],
            "duracion_estimada": 7
        }}
    ]
    
    CONTENIDO DEL CURSO:
    {texto_curso[:15000]}
    
    IMPORTANTE: Responde SOLO con el JSON válido, sin texto adicional.
    """
    
    try:
        print(f"🤖 Llamando a Gemini para generar {num_lecciones} lecciones...")
        response = model.generate_content(prompt)
        
        if not response or not response.text:
            print("❌ Gemini no devolvió respuesta")
            return []
        
        print(f"✅ Respuesta recibida de Gemini ({len(response.text)} caracteres)")
        texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
        
        lecciones = json.loads(texto_limpio)
        print(f"✅ {len(lecciones)} lecciones parseadas correctamente")
        return lecciones
        
    except json.JSONDecodeError as e:
        print(f"❌ Error parseando JSON de lecciones: {e}")
        print(f"Respuesta de IA: {response.text[:500]}...")
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
