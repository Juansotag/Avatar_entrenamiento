import logging
import os
from google import genai
from google.genai import types
from google.genai.errors import APIError

logger = logging.getLogger(__name__)

class TranscriptCorrector:
    def __init__(self, model_name="gemini-2.5-flash", api_key=None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None
        
        if self.api_key:
            # Inicializar el SDK oficial google-genai
            self.client = genai.Client(api_key=self.api_key)
        else:
            logger.warning("No se proporcionó GEMINI_API_KEY. La corrección con IA estará desactivada.")

    def chunk_transcript(self, segments, chunk_minutes=2.0):
        """
        Agrupa los segmentos de subtítulos en fragmentos de duración aproximada en minutos.
        """
        if not segments:
            return []
            
        chunks = []
        current_chunk = []
        chunk_start = segments[0]['start']
        chunk_duration_secs = chunk_minutes * 60.0
        
        for segment in segments:
            start = segment['start']
            
            # Si el segmento actual sobrepasa el límite del fragmento actual, cerramos el bloque
            if start >= chunk_start + chunk_duration_secs and current_chunk:
                end = segment['start']
                chunks.append({
                    'start': chunk_start,
                    'end': end,
                    'text': " ".join([s['text'] for s in current_chunk]),
                    'segments': current_chunk
                })
                current_chunk = [segment]
                chunk_start = start
            else:
                current_chunk.append(segment)
                
        # Agregar el último fragmento
        if current_chunk:
            end = current_chunk[-1]['start'] + current_chunk[-1].get('duration', 0.0)
            chunks.append({
                'start': chunk_start,
                'end': end,
                'text': " ".join([s['text'] for s in current_chunk]),
                'segments': current_chunk
            })
            
        return chunks

    def _format_time(self, seconds):
        """Formatea segundos en formato MM:SS o HH:MM:SS."""
        secs = int(seconds)
        hours = secs // 3600
        mins = (secs % 3600) // 60
        secs = secs % 60
        if hours > 0:
            return f"{hours:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"

    def correct_chunk(self, raw_text, start_time, end_time, prev_corrected_text=""):
        """
        Corrige un fragmento de texto usando Gemini API, manteniendo coherencia con el fragmento anterior.
        """
        if not self.client:
            # Fallback si no hay API Key: retornar el texto crudo tal cual
            return raw_text

        time_range = f"[{self._format_time(start_time)} - {self._format_time(end_time)}]"
        
        # Diseñar el prompt con el rol e instrucciones precisas
        system_instruction = (
            "Eres un editor y transcriptor profesional. Tu tarea es corregir y mejorar la calidad de subtítulos "
            "autogenerados de YouTube (transcripción de audio a texto) en español. "
            "Instrucciones:\n"
            "1. Corrige errores ortográficos, gramaticales, acentuación y puntuación (añade puntos, comas, signos de interrogación/exclamación según corresponda).\n"
            "2. Estructura el texto en oraciones y párrafos lógicos y legibles.\n"
            "3. NO resumas el contenido. NO agregues tus propios comentarios ni explicaciones adicionales.\n"
            "4. Preserva el significado original de lo expresado, el tono y las palabras del orador. "
            "Puedes omitir muletillas repetitivas (como 'eh', 'este', 'bueno') solo si dificultan severamente la lectura, "
            "pero mantén el flujo natural del discurso hablado.\n"
            "5. Devuelve ÚNICAMENTE el texto corregido, sin notas, sin formato de metadatos ni introducciones."
        )

        prompt = f"""
Contexto del segmento anterior (para dar coherencia y flujo al texto actual):
{prev_corrected_text if prev_corrected_text else '[Inicio del video]'}

Segmento crudo actual a corregir ({time_range}):
{raw_text}

Por favor, escribe a continuación únicamente la versión corregida de este segmento actual:
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2, # Baja temperatura para evitar alucinaciones y ser fiel al texto
                )
            )
            corrected_text = response.text.strip()
            # A veces Gemini puede repetir encabezados o comillas, limpiamos si es necesario
            return corrected_text
        except APIError as e:
            logger.error(f"Error de API al corregir segmento {time_range}: {e}")
            return raw_text
        except Exception as e:
            logger.error(f"Error inesperado al corregir segmento {time_range}: {e}")
            return raw_text
