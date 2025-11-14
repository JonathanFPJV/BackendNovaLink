"""
Script de verificación pre-deploy
Verifica que todo esté configurado correctamente antes de deployar
"""
import os
import sys
from pathlib import Path

def check_file_exists(filename):
    """Verifica que un archivo exista"""
    if Path(filename).exists():
        print(f"✅ {filename} encontrado")
        return True
    else:
        print(f"❌ {filename} NO encontrado")
        return False

def check_env_var(var_name, required=True):
    """Verifica que una variable de entorno esté configurada"""
    value = os.getenv(var_name)
    if value:
        print(f"✅ {var_name} configurado")
        return True
    else:
        if required:
            print(f"❌ {var_name} NO configurado (requerido)")
        else:
            print(f"⚠️  {var_name} NO configurado (opcional)")
        return not required

def main():
    print("🔍 Verificando configuración para deploy en Render...\n")
    
    all_ok = True
    
    # Verificar archivos necesarios
    print("📁 Archivos de configuración:")
    all_ok &= check_file_exists("requirements.txt")
    all_ok &= check_file_exists("Procfile")
    all_ok &= check_file_exists("render.yaml")
    all_ok &= check_file_exists(".python-version")
    all_ok &= check_file_exists("app/main.py")
    all_ok &= check_file_exists(".env.example")
    
    print("\n📦 Verificando requirements.txt:")
    with open("requirements.txt", "r") as f:
        requirements = f.read()
        required_packages = ["fastapi", "uvicorn", "sqlalchemy", "google-generativeai"]
        for pkg in required_packages:
            if pkg.lower() in requirements.lower():
                print(f"✅ {pkg} incluido")
            else:
                print(f"❌ {pkg} NO incluido")
                all_ok = False
    
    print("\n🔐 Variables de entorno (solo para desarrollo local):")
    from dotenv import load_dotenv
    load_dotenv()
    
    all_ok &= check_env_var("GOOGLE_API_KEY", required=True)
    check_env_var("CLIENT_ID", required=False)
    check_env_var("SECRET_KEY", required=False)
    check_env_var("DATABASE_URL", required=False)
    
    print("\n📋 Checklist final:")
    checklist = [
        ("Código commiteado a Git", "git status"),
        ("Archivos .env NO en Git", ".gitignore configurado"),
        ("Variables de entorno listas para Render", "GOOGLE_API_KEY, DATABASE_URL"),
        ("Documentación actualizada", "DEPLOY_RENDER.md"),
    ]
    
    for item, note in checklist:
        print(f"  • {item} ({note})")
    
    print("\n" + "="*60)
    if all_ok:
        print("✅ ¡Todo listo para deploy MVP en Render!")
        print("\n📋 Configuración Render:")
        print("Build Command:  pip install -r requirements.txt")
        print("Start Command:  uvicorn app.main:app --host 0.0.0.0 --port $PORT")
        print("Instance Type:  Free")
        print("\n🔑 Variable de Entorno Requerida:")
        print("GOOGLE_API_KEY = tu_api_key_aqui")
        print("\n🚀 Próximos pasos:")
        print("1. git add . && git commit -m 'Deploy MVP en Render'")
        print("2. git push origin main")
        print("3. Crear Web Service en Render (ver DEPLOY_RENDER_MVP.md)")
        print("4. Configurar GOOGLE_API_KEY en Variables de Entorno")
        print("5. Deploy automático comenzará")
        print("\n📚 Guías disponibles:")
        print("   - RENDER_3_PASOS.md (ultra rápida)")
        print("   - DEPLOY_RENDER_MVP.md (detallada)")
        return 0
    else:
        print("❌ Hay problemas que necesitan ser resueltos")
        print("\nRevisa los errores marcados con ❌ arriba")
        return 1

if __name__ == "__main__":
    sys.exit(main())
