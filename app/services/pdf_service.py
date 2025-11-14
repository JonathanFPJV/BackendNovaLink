"""
Servicio de procesamiento de archivos PDF
"""
from PyPDF2 import PdfReader

def extraer_texto_pdf(ruta_archivo: str) -> str:
    """Lee un PDF y devuelve todo el texto como un string"""
    reader = PdfReader(ruta_archivo)
    texto_completo = ""
    for page in reader.pages:
        texto_completo += page.extract_text()
    return texto_completo
