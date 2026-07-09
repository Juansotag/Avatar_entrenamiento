import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class YouTubeExtractor:
    def __init__(self, language_preference=['es', 'en']):
        self.language_preference = language_preference

    def get_channel_videos(self, channel_url, start_date_str, end_date_str):
        """
        Obtiene la lista de videos de un canal publicados entre start_date y end_date.
        Las fechas deben tener el formato YYYY-MM-DD.
        """
        # Convertir fechas a formato AAAAMMDD para yt-dlp
        date_after = start_date_str.replace("-", "")
        date_before = end_date_str.replace("-", "")

        ydl_opts = {
            'extract_flat': True,       # Extracción rápida de la lista
            'skip_download': True,
            'quiet': True,
            'playlistend': None,        # Sin límite de videos
            'dateafter': date_after,
            'datebefore': date_before,
        }

        logger.info(f"Buscando videos en el canal: {channel_url} entre {start_date_str} y {end_date_str}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # yt-dlp maneja URLs de canales, nombres de usuario (@nombre) e IDs
                info = ydl.extract_info(channel_url, download=False)
                
                if not info:
                    logger.warning("No se pudo obtener información del canal o URL provista.")
                    return []

                # Si es un canal, las entradas están en 'entries'
                entries = []
                if 'entries' in info:
                    entries = list(info['entries'])
                else:
                    # Si es un video individual u otro tipo de página
                    entries = [info]

                videos = []
                for entry in entries:
                    if not entry:
                        continue
                    
                    video_id = entry.get('id')
                    title = entry.get('title')
                    url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    # La fecha de subida en yt-dlp suele estar en 'upload_date' (AAAAMMDD)
                    upload_date_raw = entry.get('upload_date')
                    upload_date = None
                    if upload_date_raw:
                        try:
                            upload_date = datetime.strptime(upload_date_raw, "%Y%m%d").strftime("%Y-%m-%d")
                        except ValueError:
                            upload_date = upload_date_raw

                    # Nota: Si extract_flat=True no obtiene la fecha y yt-dlp no la filtró,
                    # haremos una validación en Python si la fecha está disponible.
                    if upload_date:
                        # Si yt-dlp no filtró por alguna razón, filtramos manualmente
                        if upload_date_raw < date_after or upload_date_raw > date_before:
                            continue

                    videos.append({
                        'id': video_id,
                        'title': title,
                        'url': url,
                        'upload_date': upload_date or "Desconocida",
                        'duration': entry.get('duration')
                    })
                
                logger.info(f"Se encontraron {len(videos)} videos en el rango de fechas.")
                return videos
            except Exception as e:
                logger.error(f"Error al listar videos del canal con yt-dlp: {e}")
                return []

    def download_transcript(self, video_id):
        """
        Descarga los subtítulos de un video en el idioma preferido.
        Retorna una lista de diccionarios con 'text', 'start', 'duration' y metadatos del idioma.
        """
        logger.info(f"Descargando subtítulos para el video: {video_id}")
        try:
            transcript_list = YouTubeTranscriptApi().list(video_id)
            
            # Buscar transcripción manual en los idiomas preferidos
            try:
                transcript = transcript_list.find_manually_created_transcript(self.language_preference)
                is_generated = False
                logger.debug(f"Subtítulos manuales encontrados para {video_id} en idioma: {transcript.language_code}")
            except Exception:
                # Buscar transcripción autogenerada
                try:
                    transcript = transcript_list.find_generated_transcript(self.language_preference)
                    is_generated = True
                    logger.debug(f"Subtítulos autogenerados encontrados para {video_id} en idioma: {transcript.language_code}")
                except Exception:
                    # Si no está en la lista de preferidos, obtener el primero disponible
                    transcript = next(iter(transcript_list))
                    is_generated = transcript.is_generated
                    logger.debug(f"Idioma preferido no disponible. Usando idioma por defecto: {transcript.language_code}")

            data = transcript.fetch()
            segments = []
            for segment in data:
                segments.append({
                    'text': segment.text,
                    'start': segment.start,
                    'duration': segment.duration
                })
            return {
                'segments': segments,
                'language_code': transcript.language_code,
                'is_generated': is_generated
            }
        except Exception as e:
            logger.warning(f"No se pudieron obtener subtítulos para el video {video_id}: {e}")
            return None
