import os
import json
import logging
import pandas as pd

logger = logging.getLogger(__name__)

class RAGFormatter:
    def __init__(self, output_dir=os.path.join("app", "data", "policy_snippets")):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        # Carpeta para archivos JSON (así no interfieren con glob("*.md") en el RAG)
        self.json_dir = os.path.join(self.output_dir, "json")
        os.makedirs(self.json_dir, exist_ok=True)

    def _format_time(self, seconds):
        """Formatea segundos en MM:SS o HH:MM:SS."""
        secs = int(seconds)
        hours = secs // 3600
        mins = (secs % 3600) // 60
        secs = secs % 60
        if hours > 0:
            return f"{hours:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"

    def _sanitize_filename(self, filename):
        """Limpia caracteres no permitidos en nombres de archivos."""
        keepcharacters = (' ', '.', '_', '-')
        return "".join(c for c in filename if c.isalnum() or c in keepcharacters).rstrip()

    def save_video_data(self, video_metadata, corrected_chunks):
        """
        Guarda los subtítulos corregidos de un video directamente como Markdown (para RAG)
        y como JSON estructurado (en una subcarpeta).
        """
        video_id = video_metadata['id']
        video_title = video_metadata['title']
        upload_date = video_metadata['upload_date']
        
        safe_title = self._sanitize_filename(video_title)
        filename_base = f"youtube_{upload_date}_{video_id}_{safe_title[:40]}"
        
        # Guardar Markdown directamente en output_dir (RAG)
        markdown_path = os.path.join(self.output_dir, f"{filename_base}.md")
        self._write_video_markdown(markdown_path, video_metadata, corrected_chunks)
        
        # Guardar JSON en json_dir
        json_path = os.path.join(self.json_dir, f"{filename_base}.json")
        self._write_video_json(json_path, video_metadata, corrected_chunks)
        
        logger.info(f"Guardados archivos de YouTube para '{video_title}':\n  - {markdown_path}\n  - {json_path}")
        return markdown_path, json_path

    def _write_video_markdown(self, file_path, video_metadata, chunks):
        """Genera el archivo Markdown del video."""
        video_id = video_metadata['id']
        video_title = video_metadata['title']
        video_url = video_metadata['url']
        upload_date = video_metadata['upload_date']

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# Transcripción de YouTube: {video_title}\n\n")
            f.write(f"- **ID del Video:** `{video_id}`\n")
            f.write(f"- **Fecha de Publicación:** {upload_date}\n")
            f.write(f"- **Enlace al Video:** [Ver en YouTube]({video_url})\n\n")
            f.write("## Contenido y Puntos Clave (con Marcas de Tiempo)\n\n")
            
            for chunk in chunks:
                start_sec = int(chunk['start'])
                time_str = self._format_time(start_sec)
                timestamp_link = f"[{time_str}]({video_url}&t={start_sec})"
                f.write(f"**{timestamp_link}** {chunk['text_corrected']}\n\n")

    def _write_video_json(self, file_path, video_metadata, chunks):
        """Genera el archivo JSON del video."""
        video_id = video_metadata['id']
        video_title = video_metadata['title']
        video_url = video_metadata['url']
        upload_date = video_metadata['upload_date']

        rag_documents = []
        for i, chunk in enumerate(chunks):
            start_sec = int(chunk['start'])
            time_str = self._format_time(start_sec)
            chunk_url = f"{video_url}&t={start_sec}"
            
            doc = {
                "type": "youtube",
                "chunk_id": f"yt_{video_id}_{i:03d}",
                "video_id": video_id,
                "video_title": video_title,
                "video_url": video_url,
                "chunk_url": chunk_url,
                "upload_date": upload_date,
                "start_time": chunk['start'],
                "end_time": chunk['end'],
                "timestamp_formatted": time_str,
                "text_raw": chunk['text_raw'],
                "text_corrected": chunk['text_corrected']
            }
            rag_documents.append(doc)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(rag_documents, f, indent=2, ensure_ascii=False)

    def save_tweets_data(self, handle, df_tweets, start_date, end_date):
        """
        Guarda los tweets extraídos en formato Markdown en la carpeta RAG y JSON en subcarpeta.
        """
        if df_tweets.empty:
            logger.warning(f"No hay tweets para guardar para @{handle}")
            return None, None

        handle_clean = handle.strip('@')
        filename_base = f"twitter_{handle_clean}"
        
        # 1. Guardar Markdown directamente en output_dir (RAG)
        markdown_path = os.path.join(self.output_dir, f"{filename_base}.md")
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(f"# Publicaciones de Twitter de @{handle_clean}\n\n")
            f.write(f"- **Cuenta:** [@{handle_clean}](https://x.com/{handle_clean})\n")
            f.write(f"- **Rango de Búsqueda:** desde {start_date} hasta {end_date}\n")
            f.write(f"- **Total de Publicaciones Extraídas:** {len(df_tweets)}\n\n")
            f.write("## Listado de Publicaciones\n\n")
            
            # Ordenar por fecha descendente
            df_sorted = df_tweets.sort_values(by='date', ascending=False)
            
            for idx, row in df_sorted.iterrows():
                # Formatear fecha
                date_str = str(row['date'])
                # Si viene con huso horario e.g. "2026-05-15T12:00:00Z"
                short_date = date_str[:10] if len(date_str) >= 10 else date_str
                
                f.write(f"### Publicación ({short_date})\n\n")
                f.write(f"> {row['text']}\n\n")
                f.write(f"- **Métricas:** ❤️ {row['like_count']} Likes | 🔁 {row['retweet_count']} Reposts | 👁️ {row['view_count']} Vistas\n")
                f.write(f"- **Enlace Directo:** [Ver en X]({row['url']})\n\n")
                f.write("---\n\n")

        # 2. Guardar JSON en json_dir
        json_path = os.path.join(self.json_dir, f"{filename_base}.json")
        tweets_list = df_tweets.to_dict(orient='records')
        # Agregar campo 'type' para RAG
        for t in tweets_list:
            t['type'] = 'twitter'
            
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(tweets_list, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Guardados archivos de Twitter para @{handle_clean}:\n  - {markdown_path}\n  - {json_path}")
        return markdown_path, json_path

    def create_unified_database(self, all_videos_data, all_tweets_data, output_filename="db_rag_unified.json"):
        """
        Crea una base de datos consolidada JSON con todos los fragmentos y tweets procesados.
        """
        consolidated_db = []
        
        # 1. Agregar datos de YouTube
        for video_metadata, corrected_chunks in all_videos_data:
            video_id = video_metadata['id']
            video_title = video_metadata['title']
            video_url = video_metadata['url']
            upload_date = video_metadata['upload_date']

            for i, chunk in enumerate(corrected_chunks):
                start_sec = int(chunk['start'])
                time_str = self._format_time(start_sec)
                chunk_url = f"{video_url}&t={start_sec}"
                
                doc = {
                    "type": "youtube",
                    "chunk_id": f"yt_{video_id}_{i:03d}",
                    "video_id": video_id,
                    "video_title": video_title,
                    "video_url": video_url,
                    "chunk_url": chunk_url,
                    "upload_date": upload_date,
                    "start_time": chunk['start'],
                    "end_time": chunk['end'],
                    "timestamp_formatted": time_str,
                    "text_raw": chunk['text_raw'],
                    "text_corrected": chunk['text_corrected']
                }
                consolidated_db.append(doc)

        # 2. Agregar datos de Twitter
        for handle, df_tweets in all_tweets_data:
            if df_tweets.empty:
                continue
            tweets_list = df_tweets.to_dict(orient='records')
            for i, tweet in enumerate(tweets_list):
                date_str = str(tweet['date'])
                doc = {
                    "type": "twitter",
                    "chunk_id": f"tw_{handle.strip('@')}_{i:03d}",
                    "account": handle.strip('@'),
                    "upload_date": date_str[:10] if len(date_str) >= 10 else date_str,
                    "video_title": f"Tweet de @{handle.strip('@')}", # Mapear llave para homogeneidad si necesario
                    "chunk_url": tweet['url'],
                    "text_raw": tweet['text'],
                    "text_corrected": tweet['text'],
                    "like_count": tweet['like_count'],
                    "retweet_count": tweet['retweet_count'],
                    "view_count": tweet['view_count']
                }
                consolidated_db.append(doc)

        unified_path = os.path.join(self.output_dir, output_filename)
        with open(unified_path, 'w', encoding='utf-8') as f:
            json.dump(consolidated_db, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Creada base de datos RAG consolidada en: {unified_path} con {len(consolidated_db)} elementos en total.")
        return unified_path
