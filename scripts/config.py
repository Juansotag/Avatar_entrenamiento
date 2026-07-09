import os
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
load_dotenv()

class Config:
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description="Herramienta unificada para extraer, corregir y formatear datos de YouTube y Twitter para el RAG del Simulador."
        )
        self._setup_args()
        
    def _setup_args(self):
        self.parser.add_argument(
            "--channel", "-c",
            default=None,
            help="URL del canal de YouTube (ej. https://www.youtube.com/@Canal) o ID del canal para extraer subtítulos."
        )
        self.parser.add_argument(
            "--twitter", "-t",
            default=None,
            help="Nombre de usuario / handle de Twitter (ej. @SenadoGovCo o SenadoGovCo) para extraer publicaciones."
        )
        self.parser.add_argument(
            "--start-date", "-s",
            required=True,
            help="Fecha de inicio en formato YYYY-MM-DD."
        )
        self.parser.add_argument(
            "--end-date", "-e",
            required=True,
            help="Fecha de fin en formato YYYY-MM-DD."
        )
        self.parser.add_argument(
            "--output-dir", "-o",
            default=os.path.join("app", "data", "policy_snippets"),
            help="Directorio donde se guardarán los fragmentos Markdown para el RAG (por defecto: 'app/data/policy_snippets')."
        )
        self.parser.add_argument(
            "--model", "-m",
            default="gemini-2.5-flash",
            help="Modelo de Gemini a utilizar para corregir subtítulos (por defecto: 'gemini-2.5-flash')."
        )
        self.parser.add_argument(
            "--chunk-minutes", "-p",
            type=float,
            default=2.0,
            help="Duración en minutos de cada bloque de subtítulo (por defecto: 2.0)."
        )
        self.parser.add_argument(
            "--language", "-l",
            default="es",
            help="Código de idioma preferido para subtítulos de YouTube (por defecto: 'es')."
        )
        self.parser.add_argument(
            "--visible",
            action="store_true",
            help="Ejecuta el navegador de Twitter de forma visible (no-headless) para iniciar sesión manualmente la primera vez."
        )

    def parse(self):
        args = self.parser.parse_args()
        
        # Validar que al menos uno esté presente (YouTube o Twitter)
        if not args.channel and not args.twitter:
            self.parser.error("Debes especificar al menos un origen: --channel (-c) para YouTube o --twitter (-t) para Twitter.")

        # Validar fechas
        try:
            start = datetime.strptime(args.start_date, "%Y-%m-%d")
            end = datetime.strptime(args.end_date, "%Y-%m-%d")
            if start > end:
                self.parser.error("La fecha de inicio (--start-date) debe ser anterior o igual a la fecha de fin (--end-date).")
        except ValueError:
            self.parser.error("Formato de fecha inválido. Utilice YYYY-MM-DD.")
            
        # Validar API Key de Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("[ADVERTENCIA] La variable de entorno GEMINI_API_KEY no está configurada.")
            print("Asegúrate de definirla en tu entorno o en un archivo .env si deseas corregir los subtítulos de YouTube.")
            
        return args
